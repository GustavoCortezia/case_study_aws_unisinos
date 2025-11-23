# AWS Financial Dashboard Frontend

This is a Vue.js frontend project (using Vue 3, Vite, and Vuetify) that serves as an interface for a financial analysis backend hosted on AWS.
The application allows users to view financial dashboards (via Amazon QuickSight) and upload new financial statements (directly to Amazon S3) for processing.

 **Attencion:** aws_lambda.py is the file used in AWS, it has no use in this frontend project

## 🚀 Core Features

* **Dashboard Viewing:** Securely renders an Amazon QuickSight dashboard within the application by fetching an embed URL via AWS Lambda.
* **File Upload:** Allows users to upload `.csv` and `.xlsx` files directly to an S3 bucket.
* **Upload Feedback:** Includes a real-time progress bar during upload, using the `@aws-sdk/lib-storage` library.
* **Reactive UI:** Built with Vuetify 3 for a modern, responsive design.

## 🏛️ Architecture

This frontend does not store any data. It acts as a client that interacts directly with AWS services:

* **Dashboard Viewing:** The app invokes an AWS Lambda function (`getQuickSightDashboardUrl`) which generates and returns a signed embed URL from Amazon QuickSight. The app then renders this URL in an iframe.
* **File Upload:** The app uses the Cognito credentials to upload a file directly to an Amazon S3 bucket, using the `lib-storage` library for multipart uploads.

## 🛠️ Project Setup

To run this project locally, you need to configure both your AWS backend and your local development environment.

### 1. Prerequisites (AWS Backend)

Before running the app, you must have the following services configured in your AWS account:

* **Amazon S3:**
    * An S3 bucket to receive the statement files.
    * **CORS Configuration:** You MUST configure CORS on your bucket to allow uploads from your development environment. Go to your bucket's "Permissions" -> "CORS" and add:

    ```json
    [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["PUT", "POST", "GET"],
            "AllowedOrigins": [
                "http://localhost:3000",
                "[http://127.0.0.1:3000](http://127.0.0.1:3000)"
            ],
            "ExposeHeaders": ["ETag"]
        }
    ]
    ```

* **AWS Lambda:**
    * A Lambda function (e.g., `getQuickSightDashboardUrl`) with permission to generate QuickSight embed URLs.

* **Amazon QuickSight:**
    * A dashboard ready to be displayed.

* **Amazon Cognito (Recommended for Security):**
    * An Identity Pool configured to allow "guest" (unauthenticated) or authenticated access.
    * The IAM Roles for this pool must have permission to:
        * Invoke the Lambda function (`lambda:InvokeFunction`).
        * Upload objects to S3 (`s3:PutObject`).

### 2. Setup (Local Frontend)

This project uses environment variables to securely store your AWS configuration keys instead of hard-coding them.

1.  **Clone the repository:**
    ```bash
    git clone https://your-repository/project.git
    cd project
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Create your environment file:**
    * Create a file named `.env.local` in the project root.
    * > **IMPORTANT:** Add `.env.local` to your `.gitignore` file to never commit your keys!

4.  **Add variables to `.env.local`:**
    ```ini
    VITE_AWS_REGION=us-east-2
    VITE_AWS_COGNITO_IDENTITY_POOL_ID=us-east-2:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    VITE_AWS_S3_BUCKET_NAME=your-statements-bucket
    ```

5.  **Check `src/aws-config.js`:**
    * Ensure this file is reading the environment variables (`import.meta.env.VITE_...`) to initialize the S3 and Lambda clients.

## ධ Run Locally

After configuration, start the development server:

```bash
npm run dev