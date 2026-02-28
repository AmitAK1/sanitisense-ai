# Infrastructure Setup Notes (Person C — You, Amit)

## 📋 Day 1 Priority: Get AWS Resources Running

### Step 1: Verify Bedrock Model Access (DO THIS FIRST!)
Bedrock models are now auto-enabled — no manual activation needed.
Just verify it works by going to:
1. AWS Console → Amazon Bedrock → Model catalog → Claude 3 Sonnet → Open in Playground
2. Send a test message like "Hello" — if it responds, you're good!
3. For Anthropic models: first-time users may need to submit use case details (one-time)
4. Models needed: **Claude 3 Sonnet** (image+text) + **Titan Text Embeddings V2** (RAG)

### Step 2: Create DynamoDB Table
```bash
aws dynamodb create-table \
  --table-name SanitiSense \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    'IndexName=GSI1,KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
  --billing-mode PAY_PER_REQUEST
```

### Step 3: Create S3 Buckets
```bash
aws s3 mb s3://sanitisense-media-YOUR_ACCOUNT_ID
aws s3 mb s3://sanitisense-knowledge-YOUR_ACCOUNT_ID

# Enable CORS on media bucket
aws s3api put-bucket-cors --bucket sanitisense-media-YOUR_ACCOUNT_ID --cors-configuration '{
  "CORSRules": [{
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["*"],
    "MaxAgeSeconds": 3600
  }]
}'
```

### Step 4: Deploy Backend with SAM
```bash
cd infrastructure
sam build
sam deploy --guided
# Stack name: sanitisense-backend
# Region: us-east-1
# Confirm changes: Y
# Allow SAM to create IAM roles: Y
```
**Save the API URL from the output — Person A needs it!**

### Step 5: Create Bedrock Knowledge Base (RAG)
1. Go to AWS Console → Amazon Bedrock → Knowledge Bases
2. Create knowledge base:
   - Name: `SanitiSense-Health-KB`
   - Data source: S3 bucket `sanitisense-knowledge-*`
   - Embeddings model: **Amazon Titan Text Embeddings V2**
3. Upload these docs to the knowledge bucket:
   - WHO WASH guidelines (download from WHO website)
   - India disease surveillance data
   - Dengue/Malaria prevention protocols
4. Sync the knowledge base
5. Copy the Knowledge Base ID → update Lambda env vars

### Step 6: Seed Demo Data
```bash
cd infrastructure
pip install boto3
# Uncomment the boto3 lines in seed_data.py first
python seed_data.py
```

### Step 7: Setup Amplify (Day 2-3)
1. Go to AWS Console → AWS Amplify
2. Connect GitHub repo: `AmitAK1/sanitisense-ai`
3. Branch: `main`
4. Build settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `.next`
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = your API Gateway URL from Step 4
6. Deploy!

## 🔑 Environment Variables to Share with Team
After deploying, share these with Person A and B:
```
API_URL=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
TABLE_NAME=SanitiSense
S3_BUCKET=sanitisense-media-YOUR_ACCOUNT_ID
KNOWLEDGE_BASE_ID=xxxxxxxx
AWS_REGION=us-east-1
```

## ⏰ Time Estimates
- Bedrock model access: 5 min
- DynamoDB + S3: 10 min
- SAM deploy: 15 min
- Knowledge Base: 30 min
- Seed data: 5 min
- Amplify setup: 15 min
- **Total: ~1.5 hours**
