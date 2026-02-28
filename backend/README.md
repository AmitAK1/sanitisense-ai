# SanitiSense AI — Backend (Lambda Functions)

## Owner: Person B (Backend Developer)

## Tech Stack
- Python 3.12
- boto3 (AWS SDK)
- All functions run as AWS Lambda (Person C deploys them)

## Setup (Local Development)
```bash
cd backend
pip install -r requirements.txt

# Test locally:
python -c "from lambdas.report_processor import handler; print(handler({'body': '{}'}, None))"
```

## Lambda Functions to Build

### 1. `report_processor.py` — Process New Citizen Report
**Trigger:** POST /reports
**Input:**
```json
{
  "image_key": "citizen-reports/2026/02/28/abc123.jpg",
  "latitude": 19.0760,
  "longitude": 72.8777,
  "voice_key": "citizen-reports/2026/02/28/abc123.webm"  // optional
}
```
**What it does:**
1. Generate unique ticket ID (e.g., "SAN" + 6 random digits)
2. Call `image_analyzer` logic (or invoke it separately)
3. Save report to DynamoDB
4. Return ticket ID + AI analysis

**Output:**
```json
{
  "ticket_id": "SAN123456",
  "status": "pending",
  "ai_analysis": {
    "category": "garbage_pile",
    "severity_score": 8,
    "description": "Large pile of mixed waste...",
    "is_spam": false,
    "health_risk": "high"
  }
}
```

### 2. `image_analyzer.py` — Bedrock + Rekognition Analysis
**What it does:**
1. Read image from S3 (using `image_key`)
2. Call Amazon Bedrock (Claude 3 Sonnet) with the image — see PROMPT below
3. Call Amazon Rekognition DetectLabels for supplementary labels
4. Return merged analysis JSON

**Bedrock Prompt (hardcode this):**
```python
CLASSIFICATION_PROMPT = """Analyze this photo taken by a citizen reporting a sanitation issue in an Indian city.

Return ONLY a valid JSON object with these fields:
{
  "is_spam": boolean,
  "category": "garbage_pile" | "overflowing_drain" | "blocked_sewer" | "stagnant_water" | "medical_waste" | "animal_carcass" | "other",
  "severity_score": integer 1-10,
  "description": "2-3 sentence human-readable description",
  "health_risk": "none" | "low" | "medium" | "high",
  "confidence": float 0.0-1.0
}

Severity guide: 1-3 minor litter, 4-6 moderate, 7-8 large piles/blocked drains, 9-10 bio-hazards/medical waste."""
```

**Bedrock API call pattern:**
```python
import boto3
import json
import base64

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def analyze_image(image_bytes):
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": CLASSIFICATION_PROMPT
                    }
                ]
            }]
        })
    )
    
    result = json.loads(response['body'].read())
    return json.loads(result['content'][0]['text'])
```

### 3. `task_manager.py` — Worker Task CRUD
**Endpoints:**
- `GET /tasks?worker_id=xxx` — list tasks assigned to worker
- `POST /tasks/{task_id}/start` — mark task as in-progress
- `POST /tasks/{task_id}/complete` — submit after-photo, trigger validation

### 4. `validation.py` — Before/After Comparison
**Input:** before_image_key + after_image_key
**What it does:**
1. Read both images from S3
2. Send both to Bedrock Claude 3 Sonnet Vision
3. Ask it to compare and estimate waste reduction %

**Bedrock Prompt:**
```python
VALIDATION_PROMPT = """Compare these two photos of the same location.
Image 1 (BEFORE): Shows the area before cleanup.
Image 2 (AFTER): Shows the area after cleanup.

Return ONLY valid JSON:
{
  "waste_reduction_percent": integer 0-100,
  "validation_status": "approved" | "partial" | "rejected",
  "same_location": boolean,
  "assessment": "2-3 sentence explanation",
  "suspicious": boolean
}

Rules: approved = >=70% reduction, partial = 40-69%, rejected = <40% or suspicious."""
```

### 5. `dashboard_api.py` — Dashboard Statistics
**Endpoint:** GET /dashboard/stats
**Returns:** Aggregated stats from DynamoDB

### 6. `epidemic_advisor.py` — AI Health Risk Advisory
**Endpoint:** GET /dashboard/epidemic?zone=xxx
**What it does:**
1. Query DynamoDB for reports in a geographic zone
2. Summarize the cluster data
3. Send to Bedrock asking for disease risk assessment
4. Return advisory text

## Environment Variables (Person C will set these in Lambda)
```
S3_BUCKET=sanitisense-media
DYNAMODB_TABLE=sanitisense-main
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_REGION=us-east-1
```

## DynamoDB Table Structure
```
Table: sanitisense-main
- PK (Partition Key): pk  (String)  — e.g., "REPORT#SAN123456"
- SK (Sort Key): sk  (String)  — e.g., "METADATA"

Example items:
{pk: "REPORT#SAN123456", sk: "METADATA", ticket_id: "SAN123456", category: "garbage_pile", severity: 8, status: "pending", lat: 19.07, lng: 72.87, created_at: "2026-02-28T10:00:00Z"}
{pk: "TASK#T001", sk: "METADATA", report_ticket: "SAN123456", worker_id: "W001", status: "assigned", priority: 1}
```
