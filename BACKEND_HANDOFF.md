# SanitiSense AI — Backend Handoff Document

> **Purpose:** This document defines the exact API contracts, data shapes, and backend tasks needed so that the **backend person** can build/fix Lambda functions while the **frontend person** builds new UI features — with zero mismatch.
>
> **Deadline:** March 4, 2026 — 11:59 PM IST  
> **API Base URL:** `https://rh74yspy85.execute-api.us-east-1.amazonaws.com/prod`

---

## Table of Contents
1. [What's Already Working](#1-whats-already-working)
2. [What Frontend Will Build (and what it expects)](#2-what-frontend-will-build)
3. [NEW API Endpoints Needed](#3-new-api-endpoints-needed)
4. [EXISTING API Fixes Needed](#4-existing-api-fixes-needed)
5. [S3 Presigned URL Flow](#5-s3-presigned-url-flow)
6. [Bedrock Knowledge Base Setup](#6-bedrock-knowledge-base-setup)
7. [DynamoDB Schema Reference](#7-dynamodb-schema-reference)
8. [Environment & Deployment](#8-environment--deployment)

---

## 1. What's Already Working

### Deployed Lambda Functions (6 total)
| Lambda | File | Route | Status |
|--------|------|-------|--------|
| `report_processor` | `backend/lambdas/report_processor.py` | `POST /reports` | ✅ Deployed — but returns **mock** AI analysis (hardcoded category/severity) |
| `image_analyzer` | `backend/lambdas/image_analyzer.py` | `POST /analyze` | ✅ Deployed — Bedrock + Rekognition code ready, needs **real S3 images** to work |
| `task_manager` | `backend/lambdas/task_manager.py` | `GET/POST/PUT /tasks`, `GET /worker/{id}/tasks` | ✅ Deployed — real DynamoDB CRUD |
| `validation` | `backend/lambdas/validation.py` | `POST /validate` | ✅ Deployed — Bedrock code ready, needs **real S3 images** |
| `epidemic_advisor` | `backend/lambdas/epidemic_advisor.py` | `GET /epidemic?ward=X` | ❌ **Broken** — `KNOWLEDGE_BASE_ID` is still `YOUR_KB_ID` |
| `dashboard_api` | `backend/lambdas/dashboard_api.py` | `GET /dashboard` | ✅ Deployed — reads **real DynamoDB data** (50 seeded reports) |

### Infrastructure
- **DynamoDB Table:** `SanitiSense` (PK/SK + GSI1)
- **S3 Media Bucket:** `sanitisense-media-982253889131` (CORS enabled)
- **S3 Knowledge Bucket:** `sanitisense-knowledge-982253889131` (empty — for RAG docs)
- **Bedrock Model:** `us.anthropic.claude-sonnet-4-20250514-v1:0` (CONFIRMED working)
- **SAM Stack:** `sanitisense-backend` deployed in `us-east-1`
- **50 demo reports** seeded across 10 Mumbai wards

---

## 2. What Frontend Will Build

Here's what the frontend person will implement and what data shapes they expect from the backend:

### 2.1 Map Integration (Admin Dashboard — Leaflet.js)

**What frontend does:** Renders an interactive map using Leaflet.js with colored markers for each ward.

**Data it already gets from `GET /dashboard` → `heatmap[]`:**
```typescript
interface WardHeatmap {
  ward_number: number;     // e.g. 7
  name: string;            // e.g. "Andheri East"
  center_lat: number;      // e.g. 19.1136
  center_lng: number;      // e.g. 72.8697
  open_reports: number;    // e.g. 12
  severity_avg: number;    // e.g. 6.8
  risk_level: 'high' | 'medium' | 'low';
}
```
**Backend action:** ✅ **Already returning this data.** No change needed. Frontend will just render it on a map instead of a table.

**ADDITIONAL DATA NEEDED — Individual report markers:**
Frontend will also want to plot individual reports on the map when a ward is clicked.

**New sub-endpoint needed:**
```
GET /dashboard/reports?ward={ward_number}
```
**Expected response:**
```json
[
  {
    "report_id": "SAN-ABC123",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "category": "garbage_pile",
    "severity_score": 7,
    "status": "pending",
    "created_at": "2026-02-28T09:30:00Z",
    "description": "Large garbage pile near school..."
  }
]
```

---

### 2.2 Map on Worker View (Task Locations)

**What frontend does:** Shows a map with task locations so workers can see where to go.

**Data it already gets from `GET /tasks?status=X`:**
```typescript
interface Task {
  task_id: string;
  report_id: string;
  status: string;
  priority: string;
  sla_hours: number;
  category: string;
  severity_score: number;
  description: string;
  ward_number: number;
  assigned_worker_id: string | null;
  created_at: string;
  updated_at: string;
}
```

**PROBLEM:** Tasks currently **don't have `latitude` / `longitude`** fields. The frontend needs coordinates to place markers on a map.

**Backend fix needed:** Add `latitude` and `longitude` to the Task object.

**Updated Task shape expected by frontend:**
```typescript
interface Task {
  task_id: string;
  report_id: string;
  status: string;
  priority: string;
  sla_hours: number;
  category: string;
  severity_score: number;
  description: string;
  ward_number: number;
  latitude: number;       // ← NEW
  longitude: number;      // ← NEW
  image_key: string;      // ← NEW (before photo S3 key, for display)
  assigned_worker_id: string | null;
  created_at: string;
  updated_at: string;
}
```

**What to change in `task_manager.py`:**
- `create_task()` should copy `latitude`, `longitude`, and `image_key` from the report data into the task record
- `get_tasks_by_status()` and `get_worker_tasks()` should return these fields

---

### 2.3 S3 Image Upload from Frontend

**What frontend does:** Before submitting a report, uploads the photo to S3 using a **presigned URL**, then sends the S3 key to `POST /reports`.

**Current problem:** Frontend generates an `image_key` string but **never actually uploads the file to S3**. The backend `image_analyzer` tries to read from S3 and fails.

**NEW endpoint needed:**
```
GET /upload-url?filename=photo.jpg&content_type=image/jpeg
```

**Expected response:**
```json
{
  "upload_url": "https://sanitisense-media-982253889131.s3.amazonaws.com/citizen-reports/2026/02/28/abc123.jpg?X-Amz-Algorithm=...",
  "image_key": "citizen-reports/2026/02/28/abc123.jpg"
}
```

**Backend implementation:** Generate a presigned PUT URL using `boto3`:
```python
import boto3, uuid
from datetime import datetime

s3 = boto3.client('s3')
BUCKET = 'sanitisense-media-982253889131'

def handler(event, context):
    params = event.get('queryStringParameters') or {}
    filename = params.get('filename', 'photo.jpg')
    content_type = params.get('content_type', 'image/jpeg')
    
    ext = filename.split('.')[-1] or 'jpg'
    now = datetime.utcnow()
    key = f"citizen-reports/{now.strftime('%Y/%m/%d')}/{uuid.uuid4().hex[:8]}.{ext}"
    
    url = s3.generate_presigned_url('put_object', Params={
        'Bucket': BUCKET,
        'Key': key,
        'ContentType': content_type
    }, ExpiresIn=300)  # 5 minutes
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"upload_url": url, "image_key": key})
    }
```

**Frontend will then:**
1. `GET /upload-url?filename=photo.jpg&content_type=image/jpeg` → gets `upload_url` + `image_key`
2. `PUT {upload_url}` with raw image bytes (direct to S3)
3. `POST /reports` with `{ image_key, latitude, longitude }` (same as today)

**Also need a similar endpoint for worker after-photos:**
```
GET /upload-url?filename=after.jpg&content_type=image/jpeg&type=worker
```
This should return a key under `worker-completions/` instead of `citizen-reports/`.

---

### 2.4 Report Processor → Actually Call Image Analyzer

**Current problem:** `report_processor.py` returns **hardcoded mock AI analysis**:
```python
# TODO: Call image_analyzer to get AI classification
ai_analysis = {
    "is_spam": False,
    "category": "garbage_pile",
    "severity_score": 7,
    ...
}
```

**What needs to happen:** After the citizen uploads a real photo to S3, `report_processor` should:
1. Invoke `image_analyzer` Lambda (or call Bedrock directly) with the `image_key`
2. Use the **real** AI result for the report
3. Auto-create a Task via `task_manager.create_task()`

**Expected flow:**
```
Frontend → POST /reports {image_key, lat, lng}
  → report_processor Lambda:
      1. Call image_analyzer(image_key) → get real AI classification
      2. If is_spam=true → return spam rejection, don't create task
      3. If is_spam=false → save report to DynamoDB with real AI data
      4. Auto-create Task via create_task() with lat/lng/image_key
      5. Return ticket_id + real ai_analysis to frontend
```

**Response shape (unchanged — frontend already expects this):**
```json
{
  "ticket_id": "SAN1A2B3C",
  "status": "pending",
  "ai_analysis": {
    "is_spam": false,
    "category": "garbage_pile",
    "severity_score": 7,
    "description": "Moderate garbage accumulation near residential area...",
    "health_risk": "medium",
    "confidence": 0.89
  },
  "message": "Report submitted successfully"
}
```

---

### 2.5 Validation Flow (Worker Completing Task)

**What frontend does:** When worker marks a task complete + uploads after-photo:
1. Upload after-photo to S3 (via presigned URL)
2. Call `POST /validate` with task_id, before_image_key, after_image_key
3. Show validation result to worker

**Current problem:** Frontend doesn't know the `before_image_key` for a task. The task object needs to include it.

**Backend fix:** Include `image_key` (the before photo) in the Task record (see section 2.2 above).

**Validation request (already defined — no change):**
```json
POST /validate
{
  "task_id": "TSK-260228-ABC123",
  "before_image_key": "citizen-reports/2026/02/28/before.jpg",
  "after_image_key": "worker-completions/2026/02/28/after.jpg"
}
```

**Validation response (already defined — no change):**
```json
{
  "task_id": "TSK-260228-ABC123",
  "validation_result": {
    "is_resolved": true,
    "resolution_quality": "good",
    "resolution_score": 8,
    "same_location": true,
    "observations": "The garbage pile has been fully removed...",
    "issues_remaining": "none",
    "confidence": 0.92
  },
  "new_status": "verified"
}
```

---

### 2.6 Epidemic Advisory Panel (Admin Dashboard)

**What frontend does:** Shows an "AI Health Risk Advisory" panel on the admin dashboard with ward-level epidemic risk predictions.

**Frontend will call:**
```
GET /epidemic?ward={ward_number}
```

**Expected response:**
```json
{
  "ward_number": 7,
  "risk_level": "high",
  "stats": {
    "open_reports": 15,
    "top_categories": "stagnant_water (6), garbage_pile (5), overflowing_drain (4)",
    "avg_severity": 7.2,
    "stagnant_water_count": 6
  },
  "advisory": "Based on WHO guidelines, the concentration of 6 stagnant water reports...",
  "diseases_at_risk": ["Dengue", "Malaria", "Leptospirosis"],
  "recommended_actions": [
    "Immediate fogging in Ward 7 — Andheri East area",
    "Deploy drainage clearing teams within 24 hours",
    "Issue citizen advisory about mosquito prevention"
  ],
  "citations": [
    {
      "text": "Stagnant water within 200m of residential areas...",
      "source": "s3://sanitisense-knowledge-982253889131/who-wash-guidelines.pdf"
    }
  ],
  "generated_at": "2026-02-28T12:00:00Z"
}
```

**Backend action needed:**
1. **Create Bedrock Knowledge Base** — upload WHO sanitation PDFs to `sanitisense-knowledge-982253889131`
2. **Update `KNOWLEDGE_BASE_ID`** in `template.yaml` and redeploy
3. Parse `advisory` text to also extract `diseases_at_risk` and `recommended_actions` arrays (frontend wants structured data, not just a wall of text)

**Fallback:** If KB not ready, the Lambda should detect `KNOWLEDGE_BASE_ID == 'YOUR_KB_ID'` and call Bedrock directly (without RAG) as a fallback, with a flag `"data_source": "bedrock_direct"` vs `"data_source": "rag"`.

---

### 2.7 City-Wide Epidemic Overview

**Frontend will call:**
```
GET /epidemic/city-overview
```

**Expected response:**
```json
{
  "city": "Mumbai",
  "overall_risk": "medium",
  "high_risk_wards": [
    { "ward_number": 7, "name": "Andheri East", "risk_level": "high", "open_reports": 15 },
    { "ward_number": 3, "name": "Byculla", "risk_level": "high", "open_reports": 12 }
  ],
  "total_open_reports": 156,
  "advisory_summary": "2 wards at high epidemic risk due to stagnant water concentration...",
  "generated_at": "2026-02-28T12:00:00Z"
}
```

**Backend action:** Currently returns a placeholder. Aggregate ward-level stats from DynamoDB and generate summary.

---

### 2.8 Role-Based Login (Simple)

**What frontend does:** Shows a role selection screen. For the hackathon prototype, we're NOT implementing real auth (no Cognito). Instead:
- User picks role: **Citizen** / **Worker** / **Admin**
- If Worker: enter a Worker ID (e.g. `W-001`)
- Frontend routes to the appropriate view

**What frontend needs from backend:**

**Worker login verification (optional but nice):**
```
GET /worker/{worker_id}/profile
```

**Expected response:**
```json
{
  "worker_id": "W-001",
  "name": "Ramesh Kumar",
  "ward_assigned": 7,
  "status": "active",
  "total_completed": 45,
  "avg_rating": 4.3
}
```

**If worker not found:**
```json
{
  "statusCode": 404,
  "error": "Worker not found"
}
```

**Backend action:** Either seed a few worker records in DynamoDB (PK: `WORKER#W-001`, SK: `PROFILE`) or auto-create on first access. This is low priority — frontend will use a hardcoded fallback if endpoint doesn't exist.

---

## 3. NEW API Endpoints Needed (Summary)

| # | Method | Path | Purpose | Priority |
|---|--------|------|---------|----------|
| 1 | `GET` | `/upload-url?filename=X&content_type=Y&type=citizen\|worker` | S3 presigned upload URL | **CRITICAL** |
| 2 | `GET` | `/dashboard/reports?ward={N}` | Individual reports for map markers in a ward | **HIGH** |
| 3 | `GET` | `/worker/{id}/profile` | Worker profile for login verification | LOW |

**Total: 3 new endpoints. Only #1 is truly new Lambda code; #2 can be added to `dashboard_api.py`; #3 can be added to `task_manager.py`.**

---

## 4. EXISTING API Fixes Needed (Summary)

| # | Lambda | What to Fix | Priority |
|---|--------|-------------|----------|
| 1 | `report_processor.py` | **Remove mock AI analysis** — call `image_analyzer` Lambda or Bedrock directly on the real S3 image | **CRITICAL** |
| 2 | `report_processor.py` | **Auto-create Task** after saving report (call `create_task` with lat/lng/image_key) | **CRITICAL** |
| 3 | `task_manager.py` | **Add `latitude`, `longitude`, `image_key`** fields to Task records and return them in API responses | **HIGH** |
| 4 | `epidemic_advisor.py` | **Create Bedrock Knowledge Base**, update KB ID, add fallback for when KB unavailable | **HIGH** |
| 5 | `epidemic_advisor.py` | **Parse structured fields** from RAG response (`diseases_at_risk`, `recommended_actions`) | **MEDIUM** |
| 6 | `dashboard_api.py` | **Add `/dashboard/reports?ward=N`** sub-endpoint returning individual report markers with lat/lng | **HIGH** |

---

## 5. S3 Presigned URL Flow (Detailed)

### Full Upload Flow (Frontend ↔ Backend ↔ S3)
```
┌──────────┐     1. GET /upload-url?filename=photo.jpg     ┌──────────┐
│ Frontend  │ ──────────────────────────────────────────────→│ Lambda   │
│ (Browser) │ ←──────────────────────────────────────────────│          │
│           │     2. { upload_url, image_key }               │          │
│           │                                                └──────────┘
│           │
│           │     3. PUT {upload_url} ← raw image bytes
│           │ ──────────────────────────────────────────────→ S3 Bucket
│           │
│           │     4. POST /reports { image_key, lat, lng }
│           │ ──────────────────────────────────────────────→│ Lambda   │
│           │ ←──────────────────────────────────────────────│          │
│           │     5. { ticket_id, ai_analysis }              │          │
└──────────┘                                                └──────────┘
```

### SAM Template Addition
```yaml
  UploadUrlFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ../backend/lambdas/
      Handler: upload_url.handler
      Events:
        GetUploadUrl:
          Type: Api
          Properties:
            RestApiId: !Ref SanitiSenseApi
            Path: /upload-url
            Method: get
      Policies:
        - S3CrudPolicy:
            BucketName: sanitisense-media-982253889131
```

---

## 6. Bedrock Knowledge Base Setup

### Steps for Backend Person
1. **Upload documents to S3:**
   ```
   aws s3 cp who-wash-guidelines.pdf s3://sanitisense-knowledge-982253889131/
   aws s3 cp dengue-prevention-protocol.pdf s3://sanitisense-knowledge-982253889131/
   aws s3 cp cholera-risk-factors.pdf s3://sanitisense-knowledge-982253889131/
   ```
   (Use any publicly available WHO WASH PDFs — at least 3 documents)

2. **Create Knowledge Base in Bedrock console:**
   - Name: `SanitiSense-Health-KB`
   - Data source: S3 bucket `sanitisense-knowledge-982253889131`
   - Embedding model: Amazon Titan Text Embeddings V2
   - Vector store: Amazon OpenSearch Serverless (auto-created by Bedrock)

3. **Sync the data source** (click "Sync" in console)

4. **Copy the KB ID** (format: `XXXXXXXXXX`) and update:
   - `infrastructure/template.yaml` → `KNOWLEDGE_BASE_ID: <actual_id>`
   - Redeploy: `sam build && sam deploy --no-confirm-changeset`

---

## 7. DynamoDB Schema Reference

### Table: `SanitiSense`

| PK Pattern | SK Pattern | Description |
|------------|------------|-------------|
| `REPORT#{ticket_id}` | `METADATA` | Citizen report with AI analysis |
| `TASK#{task_id}` | `META` | Worker task derived from report |
| `WORKER#{worker_id}` | `PROFILE` | Worker profile (NEW — to be seeded) |
| `WORKER#{worker_id}` | `TASK#{task_id}` | Worker-task assignment link |

### GSI1 (Global Secondary Index)
| GSI1PK Pattern | GSI1SK | Use Case |
|----------------|--------|----------|
| `STATUS#{status}` | `{created_at}` | Query tasks by status |

### Report Record Fields
```json
{
  "PK": "REPORT#SAN1A2B3C",
  "SK": "METADATA",
  "ticket_id": "SAN1A2B3C",
  "image_key": "citizen-reports/2026/02/28/abc123.jpg",
  "voice_key": "",
  "latitude": "19.0760",
  "longitude": "72.8777",
  "category": "garbage_pile",
  "severity_score": 7,
  "description": "Moderate garbage accumulation...",
  "health_risk": "medium",
  "is_spam": false,
  "ai_confidence": 0.89,
  "status": "pending",
  "ward_number": 7,
  "created_at": "2026-02-28T09:30:00Z",
  "updated_at": "2026-02-28T09:30:00Z"
}
```

### Task Record Fields (Updated — with lat/lng)
```json
{
  "PK": "TASK#TSK-260228-ABC123",
  "SK": "META",
  "task_id": "TSK-260228-ABC123",
  "report_id": "SAN1A2B3C",
  "status": "pending",
  "priority": "high",
  "sla_hours": 12,
  "category": "garbage_pile",
  "severity_score": 7,
  "description": "Moderate garbage accumulation...",
  "ward_number": 7,
  "latitude": 19.0760,
  "longitude": 72.8777,
  "image_key": "citizen-reports/2026/02/28/abc123.jpg",
  "assigned_worker_id": null,
  "worker_notes": "",
  "created_at": "2026-02-28T09:30:00Z",
  "updated_at": "2026-02-28T09:30:00Z",
  "GSI1PK": "STATUS#pending",
  "GSI1SK": "2026-02-28T09:30:00Z"
}
```

### Worker Profile Record (NEW — to be seeded)
```json
{
  "PK": "WORKER#W-001",
  "SK": "PROFILE",
  "worker_id": "W-001",
  "name": "Ramesh Kumar",
  "ward_assigned": 7,
  "status": "active",
  "phone": "9876543210",
  "total_completed": 45,
  "avg_rating": 4.3,
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 8. Environment & Deployment

### AWS Account
- **Account ID:** 982253889131
- **Region:** us-east-1
- **IAM User:** `sanitisense-admin`

### Key Environment Variables (in template.yaml Globals)
```yaml
TABLE_NAME: SanitiSense
S3_BUCKET: sanitisense-media-982253889131
BEDROCK_MODEL_ID: us.anthropic.claude-sonnet-4-20250514-v1:0
KNOWLEDGE_BASE_ID: YOUR_KB_ID  # ← REPLACE THIS
```

### Deploy Commands
```bash
cd infrastructure
sam build
sam deploy --no-confirm-changeset
```

### Test Locally
```bash
# Test report processor
python backend/lambdas/report_processor.py

# Test dashboard
python backend/lambdas/dashboard_api.py
```

### Git Repo
```
https://github.com/AmitAK1/sanitisense-ai.git
```

---

## Priority Order for Backend Person

| Priority | Task | Estimated Time |
|----------|------|---------------|
| 🔴 **1** | Create `upload_url.py` Lambda + add to SAM template + deploy | 1-2 hours |
| 🔴 **2** | Fix `report_processor.py` — call real Bedrock image analysis + auto-create task with lat/lng | 2-3 hours |
| 🔴 **3** | Add `latitude`, `longitude`, `image_key` to Task records in `task_manager.py` | 1 hour |
| 🟡 **4** | Add `/dashboard/reports?ward=N` endpoint in `dashboard_api.py` | 1 hour |
| 🟡 **5** | Create Bedrock Knowledge Base + upload WHO docs + update KB ID | 2-3 hours |
| 🟡 **6** | Fix `epidemic_advisor.py` — add fallback when KB unavailable, return structured fields | 1-2 hours |
| 🟢 **7** | Seed 5 worker profiles in DynamoDB | 30 min |
| 🟢 **8** | Deploy frontend to AWS Amplify (or backend person can do infra side) | 1 hour |

**Total estimated backend work: ~10-14 hours**

---

## Quick Reference: All API Routes

| Method | Path | Lambda | Status |
|--------|------|--------|--------|
| `POST` | `/reports` | report_processor | ✅ Works (mock AI) → needs real AI |
| `POST` | `/analyze` | image_analyzer | ✅ Works (needs S3 image) |
| `GET` | `/tasks?status=X` | task_manager | ✅ Works |
| `POST` | `/tasks` | task_manager | ✅ Works |
| `PUT` | `/tasks/{task_id}` | task_manager | ✅ Works |
| `GET` | `/worker/{worker_id}/tasks` | task_manager | ✅ Works |
| `POST` | `/validate` | validation | ✅ Works (needs S3 images) |
| `GET` | `/epidemic?ward=X` | epidemic_advisor | ❌ Broken (no KB) |
| `GET` | `/epidemic/city-overview` | epidemic_advisor | ❌ Placeholder |
| `GET` | `/dashboard` | dashboard_api | ✅ Real DynamoDB data |
| `GET` | `/dashboard/stats` | dashboard_api | ✅ Works |
| `GET` | `/dashboard/heatmap` | dashboard_api | ✅ Works |
| `GET` | `/dashboard/trends?days=N` | dashboard_api | ✅ Works |
| `GET` | `/dashboard/leaderboard` | dashboard_api | ✅ Works |
| `GET` | `/dashboard/recent` | dashboard_api | ✅ Works |
| `GET` | `/upload-url?filename=X` | **NEW** upload_url | 🆕 To be created |
| `GET` | `/dashboard/reports?ward=N` | dashboard_api | 🆕 To be added |
| `GET` | `/worker/{id}/profile` | task_manager | 🆕 To be added (low priority) |
