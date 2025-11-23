import { S3Client } from '@aws-sdk/client-s3';
import { LambdaClient } from '@aws-sdk/client-lambda';


const config = {

  region: import.meta.env.VITE_AWS_REGION,

  credentials: {
    accessKeyId: import.meta.env.VITE_AWS_ACCESS_KEY_ID,
    secretAccessKey: import.meta.env.VITE_AWS_SECRET_ACCESS_KEY,
  },
};


const lambdaClient = new LambdaClient(config);
const s3Client = new S3Client(config);

export {
  lambdaClient as lambda,
  s3Client as s3
};
