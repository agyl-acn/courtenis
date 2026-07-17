# Courtenis — AWS Deployment Guide

Courtenis is a tennis court booking app with an **AI agent**: users book
courts in natural language ("Book a clay court tomorrow at 3pm, my name is
Sam") and the agent checks availability, books the slot, and returns a
receipt.

This branch (`aws-deployment`) deploys Courtenis **entirely to AWS** — no
local development. You build and deploy everything from **AWS CloudShell**,
a free Linux terminal built into the AWS Console. By the end you'll have a
live URL serving the app.

```
Browser → S3 (frontend) → API Gateway → Lambda (FastAPI + AI agent) → Gemini
                                              ↓
                                          DynamoDB
```

---

## Prerequisites

- **An AWS account via the Udacity sandbox.** Log in to Udacity with your
  Accenture SSO, open the AWS course, and launch the Cloud Lab. This opens
  the AWS Console with temporary credentials.
- **Region: `us-east-1` (N. Virginia).** Confirm it in the top-right of the
  Console. Use this region for *every* service — mixing regions breaks things.
- **A free Gemini API key.** Get one at
  **https://aistudio.google.com/apikey** (sign in with any Google account →
  Create API key). The free tier is enough for this workshop.

> The Udacity AWS sandbox expires after ~1 hour. Work steadily; if the
> session ends, relaunch it and continue.

---

## How the deployed services talk to each other

Plain-language tour of the request flow:

1. The **browser** loads the React app as static files from **S3**.
2. When you chat or book, the app calls the **API Gateway** URL.
3. **API Gateway** forwards every request to the **Lambda** function.
4. Inside Lambda, **Mangum** hands the request to **FastAPI**. A chat
   message goes to the **AI agent**.
5. The agent asks **Gemini** what to do. Gemini decides which *tool* to
   call — `check_availability`, `get_courts`, or `book_slot`.
6. The chosen tool reads or writes **DynamoDB** (courts, slots, bookings).
7. The result travels back up the chain to the browser.

Lambda keeps no data itself — all state lives in DynamoDB. Its permission to
read/write DynamoDB comes from its **IAM execution role**.

---

## About the Lambda deployment zip

AWS Lambda runs your code from a zip that must contain **both your app and
all its Python dependencies**. A few things matter:

- **Built on CloudShell (Linux).** Lambda runs on Amazon Linux. Python
  packages with compiled parts (native wheels) must match that OS and
  Python version, so we build the zip on CloudShell — same platform as
  Lambda — rather than on a laptop.
- **Python 3.12 / `cp312` wheels.** The Lambda function uses the Python 3.12
  runtime, so dependencies are installed as 3.12 wheels (`cp312`).
- **`boto3`/`botocore` are stripped.** The Lambda runtime already ships the
  AWS SDK, so we delete these from the zip to stay under the size limit.
- **No `uvicorn`.** That's the local web server; on Lambda, Mangum is the
  adapter instead. Dependencies come from `requirements-lambda.txt`, not the
  full `requirements.txt`.
- **Layout:** `src/` and the dependencies sit at the **root** of the zip, so
  Lambda can import the handler `src.lambda_handler.handler`.

The result is `booking-agent/dist/lambda.zip`, roughly 43 MB.

---

## Deployment (AWS CloudShell)

Open **CloudShell** from the AWS Console top bar (the `>_` terminal icon).
Run the steps below in order. Replace every `PLACEHOLDER` with your own value.

### 1. Get the code

```bash
git clone https://github.com/agyl-acn/courtenis.git
cd courtenis
git checkout aws-deployment
```

### 2. Build the Lambda zip

```bash
cd ~/courtenis/booking-agent
rm -rf build dist/lambda.zip

pip install \
  -r requirements-lambda.txt \
  --target ./build \
  --platform manylinux2014_x86_64 \
  --python-version 3.12 \
  --implementation cp \
  --abi cp312 \
  --only-binary=:all: \
  --no-cache-dir

# Lambda already provides these — remove to shrink the zip
rm -rf build/boto3 build/botocore

cp -r src build/
cd build && zip -rq ../dist/lambda.zip . -x "*.pyc" -x "*__pycache__*" && cd ..

ls -lh dist/lambda.zip   # expect ~43 MB
```

### 3. Create the DynamoDB tables

```bash
aws dynamodb create-table --table-name courtenis_slots \
  --attribute-definitions AttributeName=slot_id,AttributeType=S \
  --key-schema AttributeName=slot_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region us-east-1

aws dynamodb create-table --table-name courtenis_bookings \
  --attribute-definitions AttributeName=booking_id,AttributeType=S \
  --key-schema AttributeName=booking_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region us-east-1

aws dynamodb create-table --table-name courtenis_courts \
  --attribute-definitions AttributeName=court_id,AttributeType=S \
  --key-schema AttributeName=court_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region us-east-1
```

### 4. Create the Lambda function

Create it once in the **Console** (this auto-creates its IAM role): go to
**Lambda → Create function**, name it `courtenis-backend`, runtime
**Python 3.12**, then **Create function**. Under **Configuration →
Permissions**, note the execution **role name**
(like `courtenis-backend-role-xxxxx`) — you'll need it in step 6.

Then upload the code and configure it from CloudShell:

```bash
aws lambda update-function-code \
  --function-name courtenis-backend \
  --zip-file fileb://dist/lambda.zip \
  --region us-east-1
sleep 15

aws lambda update-function-configuration \
  --function-name courtenis-backend \
  --handler src.lambda_handler.handler \
  --timeout 60 --memory-size 512 \
  --region us-east-1
sleep 10
```

### 5. Set the environment variables

Replace `YOUR_GEMINI_KEY` with your key from Prerequisites:

```bash
aws lambda update-function-configuration \
  --function-name courtenis-backend \
  --environment "Variables={GEMINI_API_KEY=YOUR_GEMINI_KEY,GEMINI_MODEL=gemini/gemini-2.5-flash-lite,STORAGE_BACKEND=dynamodb,SLOTS_TABLE=courtenis_slots,BOOKINGS_TABLE=courtenis_bookings,COURTS_TABLE=courtenis_courts}" \
  --region us-east-1
sleep 10
```

`STORAGE_BACKEND=dynamodb` is what makes the app use DynamoDB instead of
local SQLite.

### 6. Give Lambda permission to use DynamoDB

Replace the role name with yours from step 4:

```bash
aws iam attach-role-policy \
  --role-name courtenis-backend-role-xxxxx \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

### 7. Create the API Gateway

```bash
aws apigatewayv2 create-api \
  --name courtenis-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):function:courtenis-backend \
  --region us-east-1
```

**Copy the `ApiEndpoint` from the output — this is your backend URL**
(`https://XXXXXX.execute-api.us-east-1.amazonaws.com`). Call it `<API_URL>`
from here on.

Then let API Gateway invoke Lambda:

```bash
aws lambda add-permission \
  --function-name courtenis-backend \
  --statement-id apigw-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --region us-east-1
```

### 8. Seed the database

This fills the tables with courts and 180 days of slots. Run once:

```bash
aws lambda invoke \
  --function-name courtenis-backend \
  --payload '{"version":"2.0","routeKey":"POST /admin/seed","rawPath":"/admin/seed","requestContext":{"http":{"method":"POST","path":"/admin/seed","sourceIp":"127.0.0.1"}}}' \
  --cli-binary-format raw-in-base64-out \
  --region us-east-1 \
  response.json

cat response.json   # expect {"status":"seeded"}
```

The `sourceIp` field is required — Mangum rejects the manual invoke event
without it.

### 9. Test the backend

```bash
curl <API_URL>/health   # healthy status
curl <API_URL>/courts   # 3 courts
```

### 10. Build and deploy the frontend to S3

Build with your backend URL baked in, then host on S3. Pick a **globally
unique** bucket name.

```bash
cd ~/courtenis/frontend
npm install

VITE_API_BASE_URL=<API_URL> npm run build   # your ApiEndpoint from step 7

BUCKET=courtenis-frontend-YOURNAME-1234      # make this unique

aws s3 mb s3://$BUCKET --region us-east-1

aws s3api put-public-access-block --bucket $BUCKET \
  --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" \
  --region us-east-1

aws s3 website s3://$BUCKET --index-document index.html --error-document index.html

cat > /tmp/policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicRead",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::$BUCKET/*"
  }]
}
EOF
aws s3api put-bucket-policy --bucket $BUCKET --policy file:///tmp/policy.json

aws s3 sync dist/ s3://$BUCKET --region us-east-1

echo "Live at: http://$BUCKET.s3-website-us-east-1.amazonaws.com"
```

### 11. Try it

Open the S3 website URL in a browser:
- Click the chat button (bottom-right) and try:
  *"Any courts available on July 20 2026?"* then
  *"Book Ace Courts at 10:00, my name is [your name]"*
- Visit `/admin` to see the booking appear.

**Done — a full AI-powered app running on AWS.**

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Build fails / import errors on Lambda | Wrong Python ABI. The zip must be built with **`cp312`** wheels (Python 3.12) — do **not** use `cp313`. Rebuild on CloudShell using the exact flags in step 2. |
| Lambda crashes on a chat request | Dependency mismatch. `openai` must be pinned to **`2.44.0`** (2.45.0 breaks `openai-agents`); this pin lives in `requirements-lambda.txt`. Rebuild after any change. |
| Chatbot says "Failed to fetch" | CORS is already handled in source (`booking-agent/src/api.py` sets `allow_origins=["*"]`), so this is usually a stale deploy or wrong URL: confirm you built the frontend with the correct `<API_URL>` (step 10) and that the latest Lambda zip is uploaded, then hard-refresh (Ctrl+Shift+R). |
| Manual `lambda invoke` returns a KeyError | The invoke payload must include `requestContext.http.sourceIp`. Use the exact JSON in step 8. |
| `/courts` returns nothing / booking shows no price | Tables have stale or missing data. Re-run the seed step (step 8). Slots must carry the real court names for price lookup to work. |
| Chatbot error about quota (429) | Gemini free-tier limit hit. Wait a minute, or swap in your own `GEMINI_API_KEY`. |
| "Internal Server Error" | Check all Lambda environment variables are set (step 5). |

---

## Cleanup

Delete the Lambda `courtenis-backend`, the 3 DynamoDB tables, the API Gateway
`courtenis-api`, and empty + delete your S3 bucket — or just let the Udacity
sandbox expire (it resets automatically).
