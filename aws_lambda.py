import json
import boto3
import csv
import io
import logging
import re

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- helpers ---
AMOUNT_CLEAN_RE = re.compile(r'[^0-9\-\.,]')  # para limpar símbolo R$, espaços etc.

def parse_amount(s):
    if s is None:
        return 0.0
    s = str(s).strip()
    s = s.replace('R$', '').replace('.', '').replace(',', '.')
    s = re.sub(r'[^\d\.\-]', '', s)
    try:
        return float(s)
    except:
        try:
            return float(s.replace(' ', ''))
        except:
            return 0.0

def fix_csv_newlines(raw_text):
    """
    Junta linhas quebradas dentro de campos não-quotados corretamente.
    Lógica: acumula linhas até que o número de aspas (") no bloco seja par,
    então considera esse bloco uma linha completa do CSV.
    Retorna o CSV "limpo" como uma string com quebras de linha normais.
    """
    lines = raw_text.splitlines()
    cleaned_lines = []
    buffer = []
    quote_count = 0

    for line in lines:
        # conta aspas nesta linha
        q = line.count('"')
        buffer.append(line)
        quote_count += q

        # se o número de aspas acumuladas é par -> registro completo
        if quote_count % 2 == 0:
            # junta o bloco substituindo quebras internas por espaço
            # mantendo a integridade dos separadores
            block = '\n'.join(buffer)
            # opcional: substituir quebras internas de linha entre aspas por espaço
            # porém como garantimos que as aspas estão balanceadas, podemos normalizar
            # Substituir \r\n e \r por \n foi feito no splitlines.
            cleaned_lines.append(block)
            buffer = []
            quote_count = 0
        else:
            # ainda dentro de um campo com quebra de linha; continua acumulando
            continue

    # se sobrar algo no buffer (não balanceado), junta de qualquer forma
    if buffer:
        cleaned_lines.append('\n'.join(buffer))

    return '\n'.join(cleaned_lines)

# --- handler ---
def lambda_handler(event, context):
    # DEBUG: log do evento recebido (ajuda a ver payload do S3)
    try:
        logger.info("DEBUG - Event received:\n" + json.dumps(event, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.info(f"DEBUG - Could not dump event: {e}")

    # pega bucket e key do evento S3
    try:
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
    except Exception as e:
        logger.error(f"Event parsing error: {e}")
        return {"statusCode": 400, "body": "Invalid S3 event"}

    logger.info(f"Triggered by s3://{bucket}/{key}")

    # ler objeto do S3
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
        raw_body = resp['Body'].read().decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"S3 get_object error: {e}")
        return {"statusCode": 500, "body": "Error reading S3 object"}

    # pré-processa para corrigir quebras de linha em campos
    cleaned = fix_csv_newlines(raw_body)

    # usa csv.DictReader sobre o texto limpo
    try:
        reader = csv.DictReader(io.StringIO(cleaned))
    except Exception as e:
        logger.error(f"CSV parsing init error: {e}")
        return {"statusCode": 500, "body": "CSV parse init error"}

    rows = []
    total_income = 0.0
    total_expenses = 0.0
    per_category = {}

    # percorre linhas
    try:
        for r in reader:
            # campos comuns possíveis: amount / valor
            amount = parse_amount(r.get('amount') or r.get('valor'))
            # category / categoria fallback
            category = (r.get('category') or r.get('categoria') or 'Uncategorized').strip()
            description = (r.get('description') or r.get('descricao') or '').strip()

            rows.append({
                "description": description,
                "category": category,
                "amount": amount
            })

            if amount < 0:
                total_expenses += abs(amount)
            else:
                total_income += amount

            per_category.setdefault(category, 0.0)
            per_category[category] += amount
    except Exception as e:
        logger.error(f"Error while iterating CSV rows: {e}")
        # opcional: gravar arquivo problemático em processed/with_errors/ para análise
        error_key = 'processed/errors/' + key.split('/')[-1] + '.error.txt'
        s3.put_object(Bucket=bucket, Key=error_key, Body=raw_body.encode('utf-8'))
        logger.info(f"Saved raw problematic file to s3://{bucket}/{error_key}")
        return {"statusCode": 500, "body": "Error processing CSV rows"}

    # cria summary
    summary = {
        "file": key,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net": round(total_income - total_expenses, 2),
        "per_category": {k: round(v, 2) for k, v in per_category.items()}
    }

    out_key = 'processed/' + key.split('/')[-1] + '.summary.json'
    out_obj = {"summary": summary, "rows": rows}

    # salva processed summary no S3
    try:
        s3.put_object(Bucket=bucket, Key=out_key, Body=json.dumps(out_obj, ensure_ascii=False).encode('utf-8'))
        logger.info(f"Wrote processed file to s3://{bucket}/{out_key}")
        logger.info("Summary formatted:\n" + json.dumps(summary, indent=4, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error writing processed object: {e}")
        return {"statusCode": 500, "body": "Error saving processed file"}

    return {"statusCode": 200, "body": json.dumps(summary)}