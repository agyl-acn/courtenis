# Workshop Day 2 — Deploy an AI-Powered App to AWS

Welcome! By the end of today you will have deployed **Courtenis** — a
tennis court booking app with an AI agent — fully to AWS. The same code
that runs locally becomes a live cloud application.

**What you'll use:** Google AI Studio (Gemini), GitHub, AWS (via Udacity).

You will do the actual work in **AWS CloudShell** (a free Linux terminal
inside the Console). After each meaningful step, a **✅ Verify in Console**
section tells you exactly what to click and what you should see to confirm
it worked.

> **Time-saving tip:** AWS sandbox sessions expire after ~1 hour. Work
> steadily and don't leave long gaps. If your session ends, relaunch it
> and continue where you left off.

---

# Part 0 — Before You Start

## 0.1 Get a Google Gemini API Key

The AI agent uses Google's Gemini model. You need a free API key.

1. Go to **https://aistudio.google.com/apikey**
2. Sign in with any Google account
3. Click **Create API key**
4. Choose **Create API key in new project** (if prompted)
5. Copy the key and save it somewhere safe — you'll paste it later

> During the workshop, the facilitator may give you a shared key to
> start quickly. You can swap in your own key anytime — see
> "Using Your Own Gemini Key" at the end of this guide. The free tier
> is enough for this workshop.

## 0.2 Install Git (if you don't have it)

AWS CloudShell already has git, so you don't need it on your laptop for
this workshop. If you want to browse the code locally after the session,
check `git --version` in your terminal. If missing, download from
**https://git-scm.com/downloads**.

## 0.3 About the Code

The workshop repository has two folders:

- `booking-agent/` — the FastAPI backend + AI agent
- `frontend/` — the React web app

You'll clone the repo directly inside CloudShell in Step 1 below.

---

# Part 1 — Access AWS via Udacity

## 1.1 Log in to Udacity

1. Go to **https://www.udacity.com**
2. Log in using your **Accenture credentials** (SSO)

## 1.2 Open the AWS Course

1. Find and open the course **"AWS Cloud Architect"**
2. Enroll / start the course if you haven't already

## 1.3 Launch the Cloud Lab

1. Inside the course, find the **Cloud Resources** (or "AWS Gateway" /
   "Launch AWS Sandbox") menu
2. Click to launch — this opens the AWS Console with temporary credentials
3. **Confirm the region is N. Virginia (us-east-1)** in the top-right
   corner of the AWS Console

> **Important:** This sandbox is temporary. Use **us-east-1** for every
> service — mixing regions will cause errors.

## 1.4 Open CloudShell

In the AWS Console top bar, click the **CloudShell icon** (a terminal
symbol `>_`). Wait for it to start. This is a free Linux terminal that
runs inside AWS, in the same account and region as your Console.

You'll run all commands in this guide from CloudShell.

---

# Part 2 — Deploy the Backend

---

## Step 1: Get the Code

Clone the workshop repository into CloudShell and switch to the
deployment branch:

```bash
git clone https://github.com/agyl-acn/courtenis.git
cd courtenis
git checkout aws-deployment
```

You should see confirmation that you're on the `aws-deployment` branch.
Run `ls` to confirm you have `booking-agent/` and `frontend/` folders.

---

## Step 2: Build the Lambda Package

### What this does and why

AWS Lambda runs your code from a single zip file that must contain **both
your app source and all its Python dependencies**. Four things matter about
how we build it:

- **Built on CloudShell (Linux).** Lambda runs on Amazon Linux. Python
  packages with compiled parts must be built for the same OS and Python
  version. CloudShell is Linux, so wheels resolve correctly here — building
  on a Windows laptop would fail.
- **Python 3.12 / `cp312` wheels.** The Lambda function uses the Python 3.12
  runtime. The flags below tell pip to fetch 3.12-compatible (`cp312`) wheels.
  Do not use `cp313` — the wrong ABI causes import errors on Lambda.
- **`boto3`/`botocore` stripped.** The Lambda Python 3.12 runtime already
  ships the AWS SDK. Bundling it would add ~35 MB and push the zip over
  Lambda's upload limit. We delete them explicitly.
- **No `uvicorn`.** That's the local web server. On Lambda, the Mangum
  adapter handles that role. Dependencies come from `requirements-lambda.txt`
  (runtime-only), not the full `requirements.txt`.

The result is `dist/lambda.zip` — roughly 43 MB.

### Commands

```bash
cd ~/courtenis/booking-agent
rm -rf build dist/lambda.zip
mkdir -p dist

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

ls -lh dist/lambda.zip
```

You should see `lambda.zip` listed at around **43 MB**.

---

## Step 3: Create the DynamoDB Tables

### What this does

Creates three DynamoDB tables that will store the app's data: time slots,
bookings, and courts. `PAY_PER_REQUEST` means you're billed per operation
(no fixed capacity to provision for a workshop).

### Commands

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

### ✅ Verify in Console

Open **DynamoDB** from the Console search bar → click **Tables** in the
left sidebar. You should see **3 tables** listed:

| Table name | Status |
|---|---|
| `courtenis_courts` | Active |
| `courtenis_bookings` | Active |
| `courtenis_slots` | Active |

Wait a moment and refresh if any table still shows "Creating".

[Screenshot: DynamoDB → Tables showing 3 tables with Active status]

---

## Step 4: Create the Lambda Function

### What this does

Creates the Lambda function that will run the FastAPI backend and AI agent.
We create it in the **Console** for this step because the Console
automatically creates a proper IAM execution role. You'll need that role
name for Step 7.

### Console steps

1. Go to **Lambda** in the AWS Console (search "Lambda" in the top bar)
2. Click **Create function**
3. Leave **Author from scratch** selected
4. Function name: `courtenis-backend`
5. Runtime: **Python 3.12**
6. Leave all other settings as default
7. Click **Create function**

Once created, click **Configuration** → **Permissions**. You'll see the
**Execution role** name — it looks like `courtenis-backend-role-xxxxx`.
**Write this down or copy it** — you'll paste it in Step 7.

### ✅ Verify in Console

Lambda → **Functions** → you should see `courtenis-backend` in the list.

[Screenshot: Lambda functions list showing courtenis-backend]

---

## Step 5: Upload and Configure the Lambda Code

### What this does

Uploads your `lambda.zip` to the function and sets the handler path,
timeout, and memory. The handler `src.lambda_handler.handler` tells Lambda
where the entry point is inside the zip.

### Commands

Run these from CloudShell. The `sleep` calls give Lambda time to finish
updating between commands.

```bash
cd ~/courtenis/booking-agent

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

### ✅ Verify in Console

In the `courtenis-backend` function:

- **Code** tab → scroll to **Runtime settings** → **Handler** should show
  `src.lambda_handler.handler`
- **Configuration** tab → **General configuration** → Timeout: **1 min 0 sec**,
  Memory: **512 MB**

[Screenshot: Lambda Runtime settings panel showing the handler path]

---

## Step 6: Set the Environment Variables

### What this does

Tells Lambda your Gemini API key and how to connect to DynamoDB.
`STORAGE_BACKEND=dynamodb` is the switch that makes the app use DynamoDB
instead of the local SQLite database.

### Commands

Replace `YOUR_GEMINI_KEY` with the key you got in Part 0.1:

```bash
aws lambda update-function-configuration \
  --function-name courtenis-backend \
  --environment "Variables={GEMINI_API_KEY=YOUR_GEMINI_KEY,GEMINI_MODEL=gemini/gemini-2.5-flash-lite,STORAGE_BACKEND=dynamodb,SLOTS_TABLE=courtenis_slots,BOOKINGS_TABLE=courtenis_bookings,COURTS_TABLE=courtenis_courts}" \
  --region us-east-1
sleep 10
```

### ✅ Verify in Console

Lambda → `courtenis-backend` → **Configuration** tab → **Environment variables**.
You should see **6 variables**:

| Key | Value |
|---|---|
| `GEMINI_API_KEY` | your key (partially hidden) |
| `GEMINI_MODEL` | `gemini/gemini-2.5-flash-lite` |
| `STORAGE_BACKEND` | `dynamodb` |
| `SLOTS_TABLE` | `courtenis_slots` |
| `BOOKINGS_TABLE` | `courtenis_bookings` |
| `COURTS_TABLE` | `courtenis_courts` |

[Screenshot: Lambda Environment variables panel showing all 6 keys]

---

## Step 7: Give Lambda Permission to Use DynamoDB

### What this does

Attaches `AmazonDynamoDBFullAccess` to the Lambda execution role, allowing
the function to read and write your DynamoDB tables.

### Commands

Replace `courtenis-backend-role-xxxxx` with the role name you noted in Step 4:

```bash
aws iam attach-role-policy \
  --role-name courtenis-backend-role-xxxxx \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

No output means it succeeded.

### ✅ Verify in Console

1. Go to **IAM** → **Roles**
2. Search for your role name (`courtenis-backend-role-xxxxx`)
3. Open the role → **Permissions** tab
4. You should see **AmazonDynamoDBFullAccess** in the attached policies list

[Screenshot: IAM role permissions tab showing AmazonDynamoDBFullAccess]

---

## Step 8: Create the API Gateway

### What this does

Creates an HTTP API in front of Lambda. This is the public URL your
frontend will call. Every request to any path is forwarded to the Lambda
function (the `--target` flag wires them together automatically).

### Commands

```bash
aws apigatewayv2 create-api \
  --name courtenis-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):function:courtenis-backend \
  --region us-east-1
```

**From the output, copy the `ApiEndpoint` value** — it looks like:
`https://XXXXXX.execute-api.us-east-1.amazonaws.com`

Save it as `<API_URL>`. You'll use it in Steps 10, 11, and for testing.

Then allow API Gateway to invoke Lambda:

```bash
aws lambda add-permission \
  --function-name courtenis-backend \
  --statement-id apigw-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --region us-east-1
```

### ✅ Verify in Console

Go to **API Gateway** → **APIs**. You should see `courtenis-api` listed.
Click it → the **Invoke URL** shown should match the `ApiEndpoint` you copied.

[Screenshot: API Gateway APIs list showing courtenis-api with its Invoke URL]

---

## Step 9: Seed the Database

### What this does

Calls the `/admin/seed` endpoint to populate the DynamoDB tables with 3
courts and 180 days of available time slots. This runs once after deploying.

On Lambda, the FastAPI startup event (which seeds data locally) never fires
because Mangum runs with `lifespan="off"`. The `/admin/seed` endpoint exists
specifically for this reason and is safe to call multiple times — it only
seeds when a table is empty.

### Commands

```bash
aws lambda invoke \
  --function-name courtenis-backend \
  --payload '{"version":"2.0","routeKey":"POST /admin/seed","rawPath":"/admin/seed","requestContext":{"http":{"method":"POST","path":"/admin/seed","sourceIp":"127.0.0.1"}}}' \
  --cli-binary-format raw-in-base64-out \
  --region us-east-1 \
  response.json

cat response.json
```

You should see `{"status":"seeded"}`.

> The `sourceIp` field in the payload is required — Mangum rejects the
> manual invoke event without it.

### ✅ Verify in Console

1. Go to **DynamoDB** → **Tables** → `courtenis_courts`
2. Click **Explore table items**
3. You should see **3 courts** listed (Baseline Grounds, Net & Rally Club,
   Ace Courts)

[Screenshot: DynamoDB courtenis_courts table showing 3 court items]

---

## Step 10: Test the Backend

### Commands

Replace `<API_URL>` with your ApiEndpoint from Step 8:

```bash
curl <API_URL>/health
curl <API_URL>/courts
```

### ✅ Verify

- `/health` should return `{"status":"healthy","service":"courtenis-booking-agent"}`
- `/courts` should return a list of **3 courts**

You can also open these URLs directly in a browser tab to see the JSON.

**Backend is deployed!** Continue to Part 3 to deploy the frontend.

---

# Part 3 — Deploy the Frontend

The frontend is a React app. We build it into static files and host them
on S3, which serves them as a website.

---

## Step 11: Build the Frontend

### What this does

`npm run build` compiles the React app into plain HTML, CSS, and JavaScript
files. We pass your API Gateway URL as an environment variable so the
built app knows where to send requests.

### Commands

Replace `<API_URL>` with your ApiEndpoint from Step 8:

```bash
cd ~/courtenis/frontend
npm install

VITE_API_BASE_URL=<API_URL> npm run build

ls dist/
```

You should see `index.html` and an `assets/` folder.

---

## Step 12: Create and Configure the S3 Bucket

### What this does

Creates a publicly readable S3 bucket configured to serve static files as
a website. Bucket names must be globally unique across all AWS accounts —
use your name or initials plus a number.

### Commands

```bash
BUCKET=courtenis-frontend-YOURNAME-1234   # change this — must be globally unique

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
```

### ✅ Verify in Console

1. Go to **S3** → **Buckets** → find your bucket
2. Click it → **Properties** tab → scroll to **Static website hosting**
3. Status should be **Enabled**, and the **Bucket website endpoint** URL
   is shown — this is where your site will live

[Screenshot: S3 bucket Properties showing static website hosting enabled with endpoint URL]

---

## Step 13: Upload the Site

### Commands

```bash
aws s3 sync dist/ s3://$BUCKET --region us-east-1

echo ""
echo "Your website is live at:"
echo "http://$BUCKET.s3-website-us-east-1.amazonaws.com"
```

### ✅ Verify in Console

S3 → your bucket → **Objects** tab. You should see `index.html` and an
`assets/` folder uploaded.

[Screenshot: S3 bucket Objects tab showing index.html and assets/]

---

# Part 4 — Try It Out!

Open your S3 website URL in a browser:

```
http://BUCKET.s3-website-us-east-1.amazonaws.com
```

1. You'll see the Courtenis homepage
2. Click the **chat button** (bottom-right corner)
3. Try asking:
   - *"Any courts available on July 20 2026?"*
   - *"Book Ace Courts at 10:00, my name is [your name]"*
4. Go to `/admin` on your URL to see the booking appear in the admin panel

**Congratulations — you've deployed a full AI-powered app to AWS!**

Your app flows like this:

```
Browser → S3 (frontend) → API Gateway → Lambda (AI agent) → Gemini
                                              ↓
                                          DynamoDB
```

---

# Troubleshooting

| Problem | Fix |
|---|---|
| Build fails / import errors on Lambda | Wrong Python ABI. The zip must be built with **`cp312`** wheels (Python 3.12) — do **not** use `cp313`. Rebuild on CloudShell using the exact flags in Step 2. |
| Lambda crashes on a chat request | Dependency mismatch. `openai` must be pinned to **`2.44.0`** (2.45.0 breaks `openai-agents`); this pin is in `requirements-lambda.txt`. Rebuild after any change. |
| Chatbot says "Failed to fetch" | CORS is already handled in source (`allow_origins=["*"]`), so this is usually a stale deploy or wrong URL. Confirm you built the frontend with the correct `<API_URL>` (Step 11) and that the latest Lambda zip is uploaded, then hard-refresh (Ctrl+Shift+R). |
| Manual `lambda invoke` returns a KeyError | The invoke payload must include `requestContext.http.sourceIp`. Use the exact JSON in Step 9. |
| `/courts` returns nothing or booking shows no price | Tables have stale or missing data. Re-run the seed step (Step 9). Slots must carry the real court names for price lookup to work. |
| Chatbot error about quota (429) | Gemini free-tier limit hit. Wait a minute, or swap in your own `GEMINI_API_KEY` — see below. |
| "Internal Server Error" | Check that all 6 Lambda environment variables are set (Step 6). |

---

# Using Your Own Gemini Key

If you started with a shared key, switch to your own anytime:

1. Get your key: **https://aistudio.google.com/apikey**
2. Update the `GEMINI_API_KEY` Lambda environment variable:
   - **Console:** Lambda → `courtenis-backend` → Configuration → Environment variables → Edit
   - **CloudShell:** re-run Step 6 with your key replacing `YOUR_GEMINI_KEY`
3. Save. No rebuild needed — it takes effect on the next request.

---

# Cleanup (after the workshop)

To avoid leaving resources behind:

1. Delete the Lambda function `courtenis-backend`
2. Delete the 3 DynamoDB tables (`courtenis_slots`, `courtenis_bookings`, `courtenis_courts`)
3. Delete the API Gateway `courtenis-api`
4. Empty and delete your S3 bucket

Or simply let the Udacity sandbox expire — it resets automatically.
