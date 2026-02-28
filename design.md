# SanitiSense AI - Design Document

## Project Information

**Team Name:** Swadeshi Coders  
**Team Leader:** Amit Anil Kamble  
**Challenge Track:** [Student Track] AI for Communities, Access & Public Impact  
**Document Version:** 1.0  
**Last Updated:** February 14, 2026

---

## Quick Reference

| Aspect | Detail |
|--------|--------|
| **Architecture** | Microservices with serverless-first approach (AWS Lambda, API Gateway) |
| **Frontend** | React/Next.js (Citizen, Worker & Authority views — responsive web app) |
| **AI/ML Services** | **Amazon Bedrock (Claude 3 Sonnet — Vision + Text)**, Titan Embeddings, Bedrock Knowledge Base (RAG), Amazon Rekognition, Transcribe |
| **Database** | Amazon DynamoDB (serverless NoSQL) + Amazon S3 (object storage) |
| **Key AWS Services** | Bedrock, S3, DynamoDB, Lambda, Rekognition, Transcribe, API Gateway, Amplify, CloudWatch |
| **Generative AI** | Amazon Bedrock (Claude 3 Sonnet) for image analysis, severity scoring, before/after validation, report generation; Bedrock Knowledge Base + Titan Embeddings for RAG-based epidemic risk advisories |
| **Cost (Optimized)** | ₹1.20-₹1.50 per ticket, ₹15,000/month for 10,000 tickets |
| **Scalability** | Supports 10,000 concurrent users, 1M+ population city-wide |
| **Security** | TLS 1.3, AES-256 encryption, RBAC, GDPR compliant |
| **Offline Support** | Progressive Web App with offline-capable photo queue and background sync |

---

## Table of Contents

1. System Architecture Overview
2. Component Design
3. Technology Stack
4. AWS Services Architecture
5. Data Models
6. API Design
7. AI/ML Pipeline
8. Security Architecture
9. Deployment Strategy
10. Implementation Phases
11. Cost Analysis
12. Monitoring & Maintenance

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

SanitiSense AI follows a **microservices architecture** with three primary layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
├──────────────┬──────────────────┬─────────────────────────┤
│  Citizen     │   Worker         │  Authority Dashboard    │
│  View        │   View           │  (Map + Analytics)      │
│  (React/     │   (React/        │  (React/Next.js)        │
│   Next.js)   │    Next.js)      │                         │
│              │                  │  Deployed: AWS Amplify   │
└──────────────┴──────────────────┴─────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                       │
│                    (AWS API Gateway + JWT)                   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                       │
├──────────────┬──────────────────┬─────────────────────────┤
│ Report       │  Task            │  Analytics              │
│ Processing   │  Management      │  & Prediction           │
│ Service      │  Service         │  Service                │
│ (Lambda)     │  (Lambda)        │  (Lambda)               │
└──────────────┴──────────────────┴─────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 GENERATIVE AI SERVICES LAYER                 │
├──────────────┬──────────────────┬─────────────────────────┤
│ Amazon       │  Amazon          │  Amazon Bedrock         │
│ Bedrock      │  Bedrock KB      │  (Claude 3 Sonnet)      │
│ (Claude 3    │  + Titan         │  Before/After           │
│  Sonnet -    │  Embeddings      │  Validation &           │
│  Vision +    │  (RAG for        │  Report Generation      │
│  Text)       │  Epidemic Risk)  │                         │
├──────────────┼──────────────────┼─────────────────────────┤
│ Amazon       │  Amazon          │  Amazon                 │
│ Rekognition  │  Transcribe      │  CloudWatch             │
│ (Image       │  (Voice→Text,    │  (Monitoring)           │
│  Labels)     │  7 Languages)    │                         │
└──────────────┴──────────────────┴─────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
├──────────────┬──────────────────┬─────────────────────────┤
│ Amazon       │  Amazon S3       │  Amazon S3              │
│ DynamoDB     │  (Photos, Audio  │  (RAG Knowledge         │
│ (Reports,    │   Evidence)      │   Base Source Docs)     │
│  Tasks,      │                  │                         │
│  Users)      │                  │                         │
└──────────────┴──────────────────┴─────────────────────────┘
```

### 1.2 Architecture Principles

1. **Generative AI-First:** Amazon Bedrock (Claude 3 Sonnet) as the core intelligence layer — replaces multiple custom ML models with a single foundation model capable of vision, text analysis, and structured output
2. **Serverless-First:** AWS Lambda + DynamoDB + API Gateway for zero-ops, pay-per-use cost optimization
3. **RAG-Powered Predictions:** Amazon Bedrock Knowledge Base + Titan Embeddings for context-grounded epidemic risk advisories
4. **Offline-First:** Progressive Web App queues reports locally; syncs when connectivity available
5. **Event-Driven:** S3 triggers + DynamoDB Streams for asynchronous AI processing
6. **Cloud-Native:** 100% AWS managed services for reliability and scalability

### 1.3 Data Flow

#### Citizen Report Submission Flow
```
1. Citizen captures photo → 2. App stores locally (offline queue)
3. When online, upload to S3 → 4. Trigger Lambda function
5. Lambda sends image to Amazon Bedrock (Claude 3 Sonnet Vision):
   - Classifies issue type, scores severity 1-10, detects spam
   - Returns structured JSON
6. Amazon Rekognition provides supplementary object labels
7. If voice note: Amazon Transcribe processes audio (7 Indian languages)
8. Transcribed text → Bedrock for urgency extraction & severity adjustment
9. Store structured civic ticket in DynamoDB
10. Update Authority dashboard in real-time
```

#### Worker Task Completion Flow
```
1. Worker views assigned task → 2. Navigates to location
3. Completes cleanup → 4. Uploads "After" photo to S3
5. Trigger validation Lambda → 6. Retrieve "Before" photo from S3
7. Both images sent to Amazon Bedrock (Claude 3 Sonnet Vision):
   - "Compare these before/after images. Estimate waste reduction %"
   - Returns validation score and assessment
8. If valid (≥70% reduction) → Mark complete → Update dashboard → Close ticket
9. If invalid → Reject → Notify worker → Keep ticket open
```

#### Epidemic Risk Advisory Flow (RAG)
```
1. DynamoDB Stream detects 5+ reports in geographic cluster (30 days)
2. Lambda queries Amazon Bedrock Knowledge Base:
   - Knowledge Base sources: WHO sanitation guidelines, disease correlation data
   - Titan Embeddings index documents in vector store
   - RAG query: "Given [cluster data], assess disease outbreak risk"
3. Bedrock generates context-grounded risk advisory
4. Risk level + advisory text stored in DynamoDB
5. Authority dashboard displays AI-generated health risk panel
```

---

## 2. Component Design

### 2.1 Citizen Reporting View

**Technology:** React 18 + Next.js 14 + TypeScript  
**Target Platforms:** Responsive Web (mobile-first PWA), Android 8.0+ via browser  
**Key Features:** Offline-capable, camera integration, voice recording, zero-literacy design

#### Architecture Pattern: React Server Components + Client Components

**Modules:**
- **Photo Upload Module:** Browser camera API / file upload with client-side compression
- **Voice Recorder:** MediaRecorder API for audio capture (WebM/MP3)
- **Offline Queue:** IndexedDB for local data persistence + Service Worker for background sync
- **Location Service:** Geolocation API with fallback to IP-based location

**UI Screens:**
1. Home Screen: Single large "Report Issue" button with camera icon
2. Photo Capture: Full-screen camera/upload interface
3. Voice Note: Record/stop/play controls with waveform visualization
4. Confirmation Screen: Ticket ID display with AI classification result
5. Track Status: Simple list of submitted reports with severity badges

**Offline Capability:**
- Service Worker caches app shell for offline access
- IndexedDB stores photos + metadata (max 10 pending reports)
- Background Sync API uploads when connectivity returns
- Show sync status indicator

### 2.2 Worker Task View

**Technology:** React 18 + Next.js 14 + TypeScript  
**Target Platforms:** Responsive Web (mobile-first), Android 8.0+ via browser  
**Key Features:** Map integration, task management, before/after validation

**Modules:**
- **Map Module:** Leaflet.js / Mapbox GL for task visualization
- **Task Manager:** View, accept, complete tasks with priority sorting
- **Camera Module:** Browser camera API for after-photo capture
- **Validation Feedback:** Real-time display of Bedrock validation result

**UI Screens:**
1. Login Screen: Username/password authentication
2. Task List Screen: Prioritized list with severity indicators (color-coded)
3. Map View Screen: All assigned tasks on interactive map
4. Task Detail Screen: Before photos, AI analysis, location, description
5. Completion Screen: Upload "After" photo → instant AI validation feedback
6. Performance Dashboard: Personal stats (completion rate, validation score)

### 2.3 Authority Dashboard View

**Technology:** React 18 + Next.js 14 + TypeScript + Tailwind CSS  
**Target Platforms:** Web browsers (Chrome, Firefox, Safari)  
**Key Features:** Real-time monitoring, AI-powered analytics, RAG-based epidemic advisories

**Modules:**
- **Map Visualization:** Leaflet.js with clustered, color-coded markers
- **Analytics Engine:** Charts using Recharts/Chart.js
- **AI Advisory Panel:** Bedrock Knowledge Base (RAG) epidemic risk advisories
- **Alert System:** Real-time notifications for high-priority issues
- **Evidence Viewer:** Side-by-side before/after photo comparison with AI scores

**UI Sections:**
1. Dashboard Home: Key metrics (total reports, pending, resolved, avg time)
2. Map View: Interactive map with severity-colored markers + filters
3. Analytics: Trend charts, category breakdown, resolution time
4. **AI Epidemic Risk Panel:** RAG-generated health risk advisories per zone
5. Evidence Viewer: Before/after photos with Bedrock validation scores
6. Reports: Export data as PDF/Excel

---

## 3. Technology Stack

### 3.1 Frontend Technologies

| Component | Technology | Justification |
|-----------|------------|---------------|
| Web App (All Views) | React 18 + Next.js 14 + TypeScript | SSR, single codebase for citizen/worker/authority views, mobile-responsive |
| UI Framework | Tailwind CSS + shadcn/ui | Rapid prototyping, accessible, responsive |
| State Management | React Context + TanStack Query | Simple, efficient server state caching |
| Maps | Leaflet.js / Mapbox GL | Free, interactive, mobile-friendly |
| Deployment | **AWS Amplify** | One-click CI/CD, live URL, custom domain |

### 3.2 Backend Technologies

| Component | Technology | Justification |
|-----------|------------|---------------|
| API Gateway | **AWS API Gateway** | Managed service, auto-scaling, request throttling |
| Compute | **AWS Lambda** (Python 3.12) | Serverless, pay-per-use, auto-scaling |
| Database | **Amazon DynamoDB** | Serverless NoSQL, zero-ops, auto-scaling, single-digit ms latency |
| Object Storage | **Amazon S3** | Scalable, durable, lifecycle policies, triggers Lambda |
| Frontend Hosting | **AWS Amplify** | CI/CD, live URL, SSR support |

### 3.3 AI/ML Technologies

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Generative AI (Core)** | **Amazon Bedrock (Claude 3 Sonnet)** | Multi-modal foundation model: vision + text in one API call; classifies images, scores severity, validates cleanup, generates reports |
| **RAG Knowledge Base** | **Amazon Bedrock Knowledge Base + Titan Embeddings** | Grounds epidemic risk advisories in real health data documents; retrieval-augmented generation for accuracy |
| Image Labels | Amazon Rekognition | Supplementary structured object detection with confidence scores |
| Speech-to-Text | Amazon Transcribe | Multi-language support (7 Indian languages), custom vocabulary |
| NLP Analysis | **Amazon Bedrock (Claude 3 Sonnet)** | Urgency extraction from transcribed text; replaces Comprehend with richer contextual understanding |

### 3.4 DevOps & Monitoring

| Component | Technology | Justification |
|-----------|------------|---------------|
| CI/CD | GitHub Actions | Free for open source, easy integration |
| Infrastructure as Code | AWS CloudFormation / Terraform | Version control, reproducibility |
| Monitoring | Amazon CloudWatch | Native AWS integration, custom metrics |
| Error Tracking | AWS X-Ray | Distributed tracing, performance insights |
| Logging | CloudWatch Logs | Centralized logging, log aggregation |
| Alerting | Amazon SNS | Email/SMS notifications |

### 3.5 Optimization & Analytics

| Component | Technology | Justification |
|-----------|------------|---------------|
| Route Optimization | **Amazon Bedrock (Claude 3 Sonnet)** | Generates optimized task sequences based on priority + location (replaces OR-Tools for prototype) |
| Spatial Analysis | DynamoDB geohash queries | Lightweight geospatial clustering using geohash-based partitioning |
| Analytics | Built-in dashboard (Recharts) | Embedded in React dashboard, no extra service needed |

---

## 4. AWS Services Architecture

### 4.1 Core AWS Services

#### Amazon Bedrock (Generative AI — CORE SERVICE)
**Purpose:** Central intelligence layer for all AI tasks — replaces multiple custom ML models with a single foundation model

**Models Used:**
- **Claude 3 Sonnet (Anthropic):** Multi-modal (vision + text) foundation model
  - Image classification & severity scoring
  - Before/after cleanup validation
  - Urgency extraction from transcribed voice notes
  - Structured report generation for authorities
- **Titan Text Embeddings V2 (Amazon):** Vector embeddings for RAG

**Bedrock Knowledge Base (RAG):**
- **Data Sources:** WHO sanitation guidelines, disease-outbreak correlation studies, municipal health data (stored in S3)
- **Vector Store:** Amazon OpenSearch Serverless (managed by Bedrock KB)
- **Use Case:** When hotspot detected (5+ reports in area), RAG query generates context-grounded epidemic risk advisory
- **Why RAG:** Prevents hallucination; grounds health predictions in real medical/epidemiological data

**Key API Calls:**
```python
# Image Analysis (Vision)
bedrock.invoke_model(
    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
    body={
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "data": image_b64}},
                {"type": "text", "text": "Analyze this photo for sanitation issues. Return JSON: {category, severity_score, description, is_spam}"}
            ]
        }]
    }
)

# RAG Query (Epidemic Advisory)
bedrock_agent.retrieve_and_generate(
    knowledgeBaseId="KB_ID",
    input={"text": f"Given {cluster_data}, assess disease outbreak risk and recommend preventive measures"}
)
```

**Why Bedrock is Required (Evaluator Justification):**
1. **Multi-modal understanding:** A single API call classifies image + generates human-readable description + scores severity — no custom model training needed
2. **Contextual intelligence:** Understands code-mixed Hindi-English voice transcripts better than rule-based NLP
3. **RAG-grounded predictions:** Epidemic advisories are factually grounded in health literature, not hallucinated
4. **Before/after reasoning:** Can visually compare two images and estimate waste reduction % with natural language explanation
5. **Scalability:** Pay-per-token, no infrastructure to manage

#### Amazon S3 (Simple Storage Service)
**Purpose:** Store citizen-uploaded photos, worker completion photos, audio files

**Bucket Structure:**
```
sanitisense-media/
├── citizen-reports/
│   ├── {year}/{month}/{day}/{ticket-id}/
│   │   ├── before-1.jpg
│   │   ├── before-2.jpg
│   │   └── voice-note.mp3
├── worker-completions/
│   └── {year}/{month}/{day}/{ticket-id}/
│       └── after-1.jpg
└── ml-training-data/
    ├── garbage/
    ├── drain/
    └── spam/
```

**Configuration:**
- Lifecycle policy: Move to S3 Glacier after 90 days
- Versioning: Enabled for audit trail
- Encryption: AES-256 server-side encryption
- Access: Pre-signed URLs with 15-minute expiry

#### Amazon DynamoDB
**Purpose:** Primary database for all structured data (reports, tasks, users, analytics)

**Table Design (Single-Table Pattern):**
```
Table: sanitisense-main
├── PK: REPORT#{ticket_id}  SK: METADATA    → Report details
├── PK: REPORT#{ticket_id}  SK: MEDIA#...   → Photo/audio S3 keys
├── PK: TASK#{task_id}      SK: METADATA    → Task assignment details
├── PK: USER#{user_id}      SK: PROFILE     → User profile
├── PK: WORKER#{worker_id}  SK: TASK#...    → Worker's assigned tasks
├── PK: ZONE#{geohash}      SK: REPORT#...  → Geo-indexed reports (GSI)
└── PK: STATS#{date}        SK: DAILY       → Aggregated daily analytics

GSI-1: status-severity-index (PK: status, SK: severity_score)
GSI-2: geohash-index (PK: geohash_prefix, SK: created_at)
```

**Configuration:**
- Capacity: On-Demand (auto-scales, pay-per-request)
- Encryption: AES-256 at rest
- Point-in-time recovery: Enabled
- TTL: Auto-delete old analytics after 365 days

**Why DynamoDB over RDS:**
- Zero-ops, no schema migrations
- Single-digit millisecond latency
- Serverless — aligns with Lambda-based architecture
- Cost-effective at prototype scale (free tier: 25 WCU / 25 RCU)

#### AWS Lambda
**Purpose:** Serverless compute for API endpoints and event processing

**Functions:**
1. `report-processor`: Process new citizen reports → calls Bedrock + Rekognition
2. `image-analyzer`: Dedicated Bedrock vision analysis for complex cases
3. `voice-processor`: Trigger Transcribe + Bedrock NLP for urgency extraction
4. `task-manager`: CRUD operations for worker task assignment
5. `validation-checker`: Before/after comparison via Bedrock vision
6. `epidemic-advisor`: RAG query to Bedrock Knowledge Base
7. `dashboard-api`: Aggregate DynamoDB data for dashboard

**Configuration:**
- Runtime: Python 3.12
- Memory: 512MB - 1GB (based on function)
- Timeout: 30 seconds (API), 5 minutes (AI processing)

#### Amazon Rekognition
**Purpose:** Supplementary image label detection (structured object labels with confidence scores)

**Features Used:**
- DetectLabels: Identify objects (garbage, vehicle, building, water, etc.)
- Image Moderation: Filter inappropriate content
- Confidence scores used as additional input to Bedrock analysis

**Note:** Rekognition provides structured labels; Bedrock provides deeper contextual analysis. Together they form a robust two-layer classification system.

#### Amazon Transcribe
**Purpose:** Convert voice notes to text

**Configuration:**
- Languages: Hindi (hi-IN), English (en-IN), Marathi (mr-IN), Tamil (ta-IN), Telugu (te-IN), Bengali (bn-IN), Gujarati (gu-IN)
- Custom vocabulary: Sanitation-related terms (e.g., "kachra", "gutter", "naala")
- Output format: JSON with timestamps
- Speaker identification: Disabled (single speaker)

#### Amazon Comprehend → Replaced by Amazon Bedrock
**Note:** NLP tasks (sentiment analysis, urgency extraction, key phrase detection) are now handled by Amazon Bedrock (Claude 3 Sonnet), which provides superior contextual understanding of code-mixed Indian language text compared to Comprehend's rule-based approach.

#### Amazon API Gateway
**Purpose:** RESTful API for mobile apps and dashboard

**Endpoints:**
- POST /reports - Submit new report
- GET /reports/{id} - Get report status
- GET /tasks - Get worker tasks
- POST /tasks/{id}/complete - Mark task complete
- GET /dashboard/stats - Get dashboard metrics
- GET /hotspots - Get epidemic risk zones

**Configuration:**
- Throttling: 1000 requests/second
- Authentication: API keys + JWT tokens
- CORS: Enabled for web dashboard
- Caching: 5-minute TTL for dashboard endpoints

#### Amazon SQS (Simple Queue Service) → Simplified
**Purpose:** For prototype, S3 event triggers + DynamoDB Streams handle async processing. SQS reserved for production scale.

**Production Queues (Phase 2+):**
1. `report-processing-queue`: New reports for AI analysis
2. `notification-queue`: Alerts to send
3. `validation-queue`: Worker completion validations

#### Amazon ElastiCache → Removed for Prototype
**Note:** For prototype scope, DynamoDB on-demand mode provides sufficient read performance. ElastiCache (Redis) is planned for production Phase 2+ when dashboard query load increases.

#### AWS Amplify
**Purpose:** Frontend hosting with CI/CD and live URL

**Configuration:**
- Connected to GitHub repository
- Auto-builds on push to `main` branch
- Provides public HTTPS URL for evaluators
- Supports Next.js SSR
- Environment variables for API Gateway endpoint URL

---

## 5. Data Models

### 5.1 Database Schema (PostgreSQL + PostGIS)

#### Table: users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(15) UNIQUE,
    role VARCHAR(20) NOT NULL, -- 'citizen', 'worker', 'authority'
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

#### Table: reports
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(10) UNIQUE NOT NULL,
    citizen_id UUID REFERENCES users(id),
    location GEOGRAPHY(POINT, 4326) NOT NULL, -- PostGIS type
    address TEXT,
    landmark VARCHAR(200),
    category VARCHAR(50), -- 'garbage_pile', 'drain', etc.
    severity_score INTEGER CHECK (severity_score BETWEEN 1 AND 10),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'assigned', 'in_progress', 'completed', 'rejected'
    ai_confidence DECIMAL(5,2),
    voice_transcript TEXT,
    urgency_keywords TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_to UUID REFERENCES users(id),
    completed_at TIMESTAMP,
    is_spam BOOLEAN DEFAULT false
);

CREATE INDEX idx_reports_location ON reports USING GIST(location);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_severity ON reports(severity_score DESC);
```

#### Table: media
```sql
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(id),
    task_id UUID REFERENCES tasks(id),
    type VARCHAR(20) NOT NULL, -- 'photo_before', 'photo_after', 'voice'
    s3_key VARCHAR(500) NOT NULL,
    s3_url TEXT,
    file_size INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table: tasks
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(id),
    assigned_to UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'assigned',
    priority INTEGER CHECK (priority BETWEEN 1 AND 5),
    estimated_duration INTEGER, -- minutes
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    validation_status VARCHAR(20), -- 'pending', 'approved', 'rejected'
    validation_score DECIMAL(5,2),
    rejection_reason TEXT
);
```

#### Table: routes
```sql
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID REFERENCES users(id),
    route_date DATE NOT NULL,
    task_ids UUID[],
    total_distance DECIMAL(10,2), -- kilometers
    estimated_time INTEGER, -- minutes
    optimized_path GEOGRAPHY(LINESTRING, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table: hotspots
```sql
CREATE TABLE hotspots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    radius INTEGER DEFAULT 50, -- meters
    report_count INTEGER,
    avg_severity DECIMAL(3,1),
    risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    disease_risk_score DECIMAL(5,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table: analytics_daily
```sql
CREATE TABLE analytics_daily (
    date DATE PRIMARY KEY,
    total_reports INTEGER,
    completed_tasks INTEGER,
    avg_resolution_time INTEGER, -- minutes
    spam_filtered INTEGER,
    high_severity_count INTEGER,
    fuel_saved DECIMAL(10,2), -- liters
    distance_optimized DECIMAL(10,2) -- kilometers
);
```

---

## 6. API Design

### 6.1 RESTful API Endpoints

**Base URL:** `https://api.sanitisense.in/v1`

#### Citizen Endpoints

**POST /reports**
```json
Request:
{
  "location": {"lat": 19.0760, "lng": 72.8777},
  "photos": ["base64_encoded_image_1", "base64_encoded_image_2"],
  "voice_note": "base64_encoded_audio",
  "landmark": "Near ABC School",
  "citizen_phone": "+919876543210" // optional
}

Response (201 Created):
{
  "ticket_id": "SAN123456",
  "status": "pending",
  "estimated_resolution": "2-3 days",
  "message": "Your report has been submitted successfully"
}
```

**GET /reports/{ticket_id}**
```json
Response (200 OK):
{
  "ticket_id": "SAN123456",
  "status": "in_progress",
  "category": "garbage_pile",
  "severity": "high",
  "submitted_at": "2026-02-14T10:30:00Z",
  "assigned_to": "Worker Team A",
  "estimated_completion": "2026-02-15T16:00:00Z"
}
```

#### Worker Endpoints

**GET /tasks**
```json
Query Parameters: ?status=assigned&worker_id={uuid}

Response (200 OK):
{
  "tasks": [
    {
      "task_id": "uuid",
      "ticket_id": "SAN123456",
      "location": {"lat": 19.0760, "lng": 72.8777},
      "address": "Street 123, Ward 5",
      "category": "garbage_pile",
      "severity": 8,
      "priority": 1,
      "photos": ["https://s3.../before-1.jpg"],
      "estimated_duration": 30
    }
  ],
  "total_tasks": 12,
  "route_distance": 15.5
}
```

**POST /tasks/{task_id}/start**
```json
Request:
{
  "started_at": "2026-02-14T11:00:00Z"
}

Response (200 OK):
{
  "message": "Task started",
  "navigation_url": "https://maps.google.com/..."
}
```

**POST /tasks/{task_id}/complete**
```json
Request:
{
  "after_photos": ["base64_encoded_image"],
  "completed_at": "2026-02-14T11:30:00Z",
  "notes": "Cleaned successfully"
}

Response (200 OK):
{
  "validation_status": "approved",
  "validation_score": 92.5,
  "message": "Task completed successfully"
}

Response (400 Bad Request) - if validation fails:
{
  "validation_status": "rejected",
  "validation_score": 45.2,
  "reason": "Insufficient waste removal detected",
  "message": "Please re-clean the area"
}
```

#### Authority Endpoints

**GET /dashboard/stats**
```json
Query Parameters: ?date_from=2026-02-01&date_to=2026-02-14

Response (200 OK):
{
  "total_reports": 1250,
  "pending": 45,
  "in_progress": 23,
  "completed": 1182,
  "avg_resolution_time": 28.5,
  "spam_filtered": 87,
  "high_severity_count": 156,
  "fuel_saved": 245.5,
  "top_categories": [
    {"category": "garbage_pile", "count": 567},
    {"category": "overflowing_drain", "count": 423}
  ]
}
```

**GET /hotspots**
```json
Query Parameters: ?risk_level=high

Response (200 OK):
{
  "hotspots": [
    {
      "id": "uuid",
      "location": {"lat": 19.0760, "lng": 72.8777},
      "radius": 50,
      "report_count": 23,
      "avg_severity": 7.8,
      "risk_level": "high",
      "disease_risk_score": 85.3,
      "predicted_disease": "dengue",
      "last_updated": "2026-02-14T10:00:00Z"
    }
  ]
}
```

**GET /reports/map**
```json
Query Parameters: ?bounds=lat1,lng1,lat2,lng2&status=pending

Response (200 OK):
{
  "reports": [
    {
      "ticket_id": "SAN123456",
      "location": {"lat": 19.0760, "lng": 72.8777},
      "category": "garbage_pile",
      "severity": 8,
      "status": "pending",
      "created_at": "2026-02-14T10:30:00Z"
    }
  ],
  "total": 45
}
```

### 6.2 WebSocket API (Real-Time Updates)

**Endpoint:** `wss://api.sanitisense.in/ws`

**Events:**
- `new_report`: New citizen report submitted
- `task_assigned`: Task assigned to worker
- `task_completed`: Worker completed task
- `hotspot_alert`: New high-risk hotspot detected

---

## 7. AI/ML Pipeline

### 7.1 Image Classification Pipeline (Amazon Bedrock + Rekognition)

**Objective:** Classify sanitation issues, detect spam, score severity — all via Generative AI

**Architecture:**
```
Input Image → S3 Upload → Lambda Trigger →
  ├── Amazon Rekognition (DetectLabels) → Structured object labels
  └── Amazon Bedrock (Claude 3 Sonnet Vision) → Classification + Severity + Description
→ Merge results → Store in DynamoDB
```

**Bedrock Vision Prompt (Engineered):**
```python
prompt = """
Analyze this photo taken by a citizen reporting a sanitation issue in an Indian city.

Return a JSON object with exactly these fields:
{
  "is_spam": boolean,        // true if not a sanitation issue (selfie, food, random photo)
  "category": string,         // one of: garbage_pile, overflowing_drain, blocked_sewer, animal_carcass, medical_waste, stagnant_water, other
  "severity_score": integer,  // 1-10 scale (10=most severe)
  "description": string,      // 2-3 sentence human-readable description
  "health_risk": string,      // none, low, medium, high
  "confidence": float          // 0.0 to 1.0
}

Severity guidelines:
- 1-3: Minor litter, small debris
- 4-6: Moderate accumulation, partial drain blockage
- 7-8: Large garbage piles, fully blocked drains, stagnant water
- 9-10: Bio-hazards, medical waste, dead animals, contaminated water near residences
"""
```

**Why Bedrock Vision over Custom ML:**
1. **Zero training data required** — Claude 3 Sonnet understands sanitation images out-of-the-box
2. **Single API call** replaces 3 separate models (classifier + severity scorer + description generator)
3. **Structured JSON output** — directly usable by downstream systems
4. **Handles edge cases** — understands context (e.g., "garbage near water body" = higher severity)

**Supplementary Rekognition:**
- Provides structured `Labels[]` with `Confidence` scores
- Used as secondary validation (e.g., if Bedrock says "garbage" but Rekognition detects "Food" with 95% confidence → flag for review)

**Severity Estimation Algorithm:**
```python
def calculate_final_severity(bedrock_result, rekognition_labels, voice_urgency=0):
    base_score = bedrock_result['severity_score']
    
    # Boost if Rekognition detects high-risk objects
    HIGH_RISK_LABELS = ['Water', 'Medical', 'Animal', 'Stagnant']
    for label in rekognition_labels:
        if label['Name'] in HIGH_RISK_LABELS and label['Confidence'] > 80:
            base_score = min(base_score + 1, 10)
    
    # Add voice urgency adjustment (from Bedrock NLP)
    final_score = min(base_score + voice_urgency, 10)
    
    return max(final_score, 1)  # Clamp to 1-10
```

### 7.2 Voice Processing Pipeline (Transcribe + Bedrock NLP)

**Objective:** Transcribe voice notes and extract urgency indicators using Generative AI

**Architecture:**
```
Audio File → S3 → Amazon Transcribe (7 languages) →
Transcribed Text → Amazon Bedrock (Claude 3 Sonnet) →
Urgency Score + Context Extraction → Update DynamoDB report
```

**Process:**
1. **Audio Upload:** Citizen records voice note → stored in S3
2. **Transcription:** Amazon Transcribe converts speech to text
   - Languages: Hindi (hi-IN), English (en-IN), Marathi (mr-IN), Tamil (ta-IN), Telugu (te-IN), Bengali (bn-IN), Gujarati (gu-IN)
   - Custom vocabulary: sanitation terms ("kachra", "gutter", "naala")
3. **Bedrock NLP Analysis:**
```python
prompt = f"""
A citizen reported a sanitation issue and provided this voice note transcript:
\"{transcript}\"

Extract the following as JSON:
{{
  "urgency_adjustment": integer,  // -2 to +3 adjustment to severity score
  "duration_mentioned": string,   // how long the issue has persisted (if mentioned)
  "health_concerns": [string],    // any health concerns mentioned
  "key_context": string,          // 1-sentence summary of additional context
  "language_detected": string      // primary language of the transcript
}}

Urgency rules:
+3: Mentions children, health risk, blocked road, or emergency
+2: Mentions smell, water contamination, or weeks/months duration
+1: Mentions specific obstruction or daily impact
0: General complaint
-1: Seems uncertain or hesitant
-2: Contradicts image (e.g., says area is mostly clean)
"""
```

**Why Bedrock over Comprehend for NLP:**
- Comprehend struggles with code-mixed Hindi-English text
- Bedrock understands contextual urgency ("bacche khelte hain wahan" = children play there = +3)
- Returns structured JSON directly, no post-processing needed
```

### 7.3 Before-After Validation Pipeline (Amazon Bedrock Vision)

**Objective:** Verify actual cleanup occurred using Generative AI visual comparison

**Architecture:**
```
Before Image (S3) + After Image (S3) → Lambda →
Both images sent to Amazon Bedrock (Claude 3 Sonnet Vision) →
Validation Score + Assessment → Update DynamoDB task
```

**Bedrock Vision Prompt (Before/After Comparison):**
```python
prompt = """
You are a sanitation inspection AI. Compare these two photos of the same location.

Image 1 (BEFORE): Shows the area before cleanup.
Image 2 (AFTER): Shows the area after the sanitation worker's cleanup.

Analyze and return JSON:
{
  "waste_reduction_percent": integer,  // 0-100 estimated reduction
  "validation_status": string,         // "approved", "partial", "rejected"
  "same_location": boolean,            // do both images appear to be the same place?
  "assessment": string,                // 2-3 sentence explanation
  "suspicious": boolean                // true if photos seem staged or fake
}

Rules:
- "approved": waste_reduction_percent >= 70
- "partial": waste_reduction_percent 40-69 (needs re-cleanup)
- "rejected": waste_reduction_percent < 40 or suspicious = true
"""
```

**Why Bedrock over Custom Semantic Segmentation:**
1. **Zero training data** — no need for 10,000+ labeled before/after pairs
2. **Contextual reasoning** — can detect if photos are staged, wrong angle, or different location
3. **Natural language assessment** — provides human-readable explanation for workers and authorities
4. **Single API call** — replaces entire TensorFlow pipeline

**Validation Algorithm (with GPS check):**
```python
def validate_cleanup(before_image_s3, after_image_s3, gps_before, gps_after):
    # Step 1: GPS proximity check
    distance = haversine(gps_before, gps_after)
    if distance > 20:  # meters
        return {"valid": False, "reason": "Location mismatch", "distance": distance}
    
    # Step 2: Bedrock Vision comparison
    before_b64 = get_image_base64_from_s3(before_image_s3)
    after_b64 = get_image_base64_from_s3(after_image_s3)
    
    bedrock_result = invoke_bedrock_vision(
        images=[before_b64, after_b64],
        prompt=VALIDATION_PROMPT
    )
    
    # Step 3: Return structured result
    return {
        "valid": bedrock_result['validation_status'] == 'approved',
        "score": bedrock_result['waste_reduction_percent'],
        "status": bedrock_result['validation_status'],
        "assessment": bedrock_result['assessment'],
        "suspicious": bedrock_result['suspicious']
    }
```

### 7.4 Epidemic Prediction Pipeline (RAG via Amazon Bedrock Knowledge Base)

**Objective:** Generate context-grounded disease outbreak risk advisories using Retrieval-Augmented Generation

**Architecture:**
```
DynamoDB reports (clustered by geohash) → Lambda detects hotspot →
Assemble context (report count, severity, categories, location) →
Query Amazon Bedrock Knowledge Base (RAG) →
Titan Embeddings retrieve relevant health documents →
Claude 3 Sonnet generates grounded risk advisory →
Store advisory in DynamoDB → Display on Authority Dashboard
```

**Knowledge Base Setup:**
1. **Source Documents (stored in S3):**
   - WHO sanitation and disease correlation guidelines
   - India-specific vector-borne disease data (Dengue, Malaria, Cholera)
   - Municipal health department guidelines
   - Seasonal outbreak patterns

2. **Embeddings:** Amazon Titan Text Embeddings V2
3. **Vector Store:** Amazon OpenSearch Serverless (managed by Bedrock KB)
4. **Chunking Strategy:** Fixed-size 512 tokens with 20% overlap

**RAG Query Flow:**
```python
def generate_epidemic_advisory(hotspot_data):
    context = f"""
    Hotspot Analysis for Zone {hotspot_data['geohash']}:
    - Total reports in last 30 days: {hotspot_data['report_count']}
    - Average severity: {hotspot_data['avg_severity']}/10
    - Categories: {hotspot_data['category_breakdown']}
    - Stagnant water reports: {hotspot_data['water_reports']}
    - Current season: {hotspot_data['season']}
    - Proximity to residential areas: {hotspot_data['residential_proximity']}
    """
    
    response = bedrock_agent.retrieve_and_generate(
        knowledgeBaseId=KB_ID,
        input={
            "text": f"""
            Based on the following sanitation data and your knowledge of 
            disease-sanitation correlations, generate a health risk advisory.
            
            {context}
            
            Provide:
            1. Overall risk level (Low/Medium/High/Critical)
            2. Specific disease risks (Dengue, Malaria, Cholera, etc.)
            3. Recommended preventive actions
            4. Urgency of response needed
            """
        }
    )
    
    return {
        "risk_level": parse_risk_level(response),
        "advisory_text": response['output']['text'],
        "sources": response.get('citations', []),
        "generated_at": datetime.utcnow().isoformat()
    }
```

**Why RAG over Custom ML (XGBoost/SciKit-Learn):**
1. **No training data needed** — leverages existing health literature
2. **Grounded in facts** — RAG retrieves real medical data, preventing hallucination
3. **Explainable** — citations show which health documents informed the advisory
4. **Adaptable** — add new documents to KB without retraining
5. **Human-readable output** — generates natural language advisories, not just scores

**Scheduled Execution:**
- Lambda runs daily at 2 AM IST
- Scans DynamoDB for geographic clusters (5+ reports, geohash prefix match)
- Generates advisory for each identified hotspot
- Stores in DynamoDB with TTL of 7 days
- Triggers SNS notification for Critical risk zones

---

## 8. Security Architecture

### 8.1 Authentication & Authorization

**Citizen App:**
- Optional phone number for tracking
- Anonymous reporting allowed
- SMS OTP for status tracking

**Worker App:**
- Username/password authentication
- SMS OTP for 2FA
- JWT tokens with 24-hour expiry
- Refresh tokens for seamless experience

**Authority Dashboard:**
- Email/password authentication
- Role-Based Access Control (RBAC)
- Roles: Admin, Ward Officer, Health Official, Viewer
- JWT tokens with 8-hour expiry

**API Security:**
- API Gateway with API keys
- Rate limiting: 100 requests/minute per user
- Request signing for sensitive operations
- CORS configuration for web dashboard

### 8.2 Data Security

**Encryption:**
- **In Transit:** TLS 1.3 for all API calls
- **At Rest:** 
  - S3: AES-256 server-side encryption
  - RDS: Encryption at rest enabled
  - Secrets: AWS Secrets Manager

**Privacy:**
- GPS coordinates rounded to 10-meter precision
- No facial recognition or personal data collection
- Photos auto-deleted after 90 days (moved to Glacier)
- GDPR-compliant data handling

**Access Control:**
- S3 bucket policies: Deny public access
- RDS security groups: Whitelist Lambda IPs only
- IAM roles: Least privilege principle
- VPC: Private subnets for databases

### 8.3 Input Validation

**Image Upload:**
- File type validation: JPEG, PNG only
- File size limit: 5MB
- Malware scanning (optional: AWS GuardDuty)
- Content moderation (Rekognition)

**API Inputs:**
- Schema validation using JSON Schema
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)
- Rate limiting per endpoint

---

## 9. Deployment Strategy

### 9.1 Infrastructure as Code

**Tool:** AWS CloudFormation / Terraform

**Resources:**
- VPC with public and private subnets
- RDS instance with Multi-AZ for high availability
- Lambda functions with environment variables
- S3 buckets with lifecycle policies
- API Gateway with custom domain
- CloudWatch alarms and dashboards

### 9.2 CI/CD Pipeline

**Tool:** GitHub Actions

**Workflow:**
```yaml
1. Code Push to GitHub
2. Run Unit Tests
3. Run Integration Tests
4. Build Docker Images (for EC2 services)
5. Deploy to Staging Environment
6. Run E2E Tests
7. Manual Approval
8. Deploy to Production
9. Run Smoke Tests
10. Notify Team
```

**Environments:**
- **Development:** Local development with Docker Compose
- **Staging:** AWS environment mirroring production
- **Production:** Live environment with auto-scaling

### 9.3 Deployment Phases

**Hackathon Deliverable (During Competition - 2-3 weeks):**
- Functional prototype demonstrating core workflow
- Citizen app mockup with photo capture and upload
- Basic AI classification demo (using pre-trained models)
- Worker app mockup showing task assignment
- Dashboard prototype with map visualization
- Complete technical documentation (requirements.md, design.md)
- Presentation deck with architecture and impact analysis
- Video demo of end-to-end user journey

**Phase 1: MVP Development (Months 1-3) - Post-Hackathon**
- Production-ready citizen mobile app (Android)
  - Photo upload with GPS tagging
  - Offline capability with sync
  - Ticket tracking
- Trained AI classification model (85%+ accuracy)
  - Custom Rekognition model with 5,000+ labeled images
  - Severity scoring algorithm
  - Spam detection
- Worker mobile app
  - Task list with priority indicators
  - Google Maps integration for navigation
  - Basic task completion workflow
- Authority web dashboard
  - Real-time map view with issue markers
  - Basic analytics (reports, completions, response time)
  - Filter and search functionality
- AWS infrastructure setup
  - S3, RDS, Lambda, API Gateway
  - CI/CD pipeline
- Single ward pilot (10,000 population)
- User training and onboarding

**Deliverables:** Functional system with 100+ test users, 500+ reports processed

**Phase 2: Enhanced Features (Months 4-6)**
- Voice note support
  - Amazon Transcribe integration (7 languages)
  - NLP-based urgency extraction
  - Voice-to-text for location input
- Route optimization ("Uber for Garbage")
  - Google OR-Tools integration
  - Dynamic daily route generation
  - Turn-by-turn navigation for workers
- Before-after validation system
  - Custom semantic segmentation model
  - AI-powered cleanup verification
  - Worker performance tracking
- Basic epidemic prediction model
  - Hotspot detection using spatial clustering
  - Risk scoring based on sanitation data
  - Automated alerts to health officials
- Performance optimization
  - Caching layer (ElastiCache)
  - Database query optimization
  - Mobile app performance tuning
- Expand to 3 wards (30,000 population)

**Deliverables:** 1,000+ active users, 30% fuel savings demonstrated, 90%+ validation accuracy

**Phase 3: Scale & Optimize (Months 7-12)**
- Advanced epidemic forecasting
  - ML model trained on historical outbreak data
  - Water stagnation data integration
  - Predictive alerts with 7-day lead time
- Integration with municipal systems
  - API integration with existing ERP
  - Data sharing with health department
  - Automated ticket routing
- Comprehensive analytics
  - Advanced reporting and dashboards
  - Trend analysis and predictions
  - ROI tracking and visualization
- Multi-platform support
  - iOS app development (optional)
  - Progressive Web App for low-end devices
  - WhatsApp bot integration (optional)
- Infrastructure scaling
  - Multi-region deployment
  - Load balancing and auto-scaling
  - Disaster recovery setup
- City-wide rollout (1M+ population)
  - Phased ward-by-ward expansion
  - Training programs for 500+ workers
  - Community awareness campaigns
  - Partnership with NGOs and civic bodies

**Deliverables:** 10,000+ active users, city-wide coverage, measurable disease prevention impact, integration with government systems

### 9.4 Rollback Strategy

- Blue-Green Deployment for zero-downtime
- Database migrations with rollback scripts
- Feature flags for gradual rollout
- Automated rollback on error rate spike

---

## 10. Implementation Phases

### Hackathon Phase: Proof of Concept (2-3 weeks)

**Objective:** Demonstrate feasibility and core value proposition

**Activities:**
- Create high-fidelity mockups for all three apps
- Build basic prototype with core workflow
- Set up minimal AWS infrastructure (S3, Lambda)
- Use pre-trained models for AI demo
- Create sample dataset for demonstration
- Develop presentation and video demo
- Complete technical documentation

**Team Allocation:**
- 2 developers: Mobile app prototypes
- 1 developer: Backend API and AWS setup
- 1 developer: Dashboard mockup
- 1 designer: UI/UX and presentation

**Deliverables:**
- Working prototype (limited functionality)
- requirements.md and design.md
- Presentation deck (PDF)
- 3-minute demo video
- GitHub repository with code

**Success Criteria:**
- Demonstrate end-to-end workflow
- Show AI classification working
- Impress judges with vision and execution plan

---

### Phase 1: MVP Development (3 months) - Post-Hackathon

**Month 1: Foundation**
- Set up AWS infrastructure
- Database schema design and creation
- API Gateway and Lambda setup
- Basic citizen app (photo upload)
- S3 integration

**Month 2: AI Integration**
- Train Rekognition Custom Labels model
- Implement image classification pipeline
- Basic severity scoring
- Worker app development
- Task assignment logic

**Month 3: Dashboard & Testing**
- Authority dashboard (map view, basic stats)
- End-to-end testing
- User acceptance testing with pilot group
- Bug fixes and optimization
- Pilot launch in one ward

**Deliverables:**
- Functional citizen and worker apps
- Basic AI classification (85%+ accuracy)
- Simple dashboard
- 100+ test users

### Phase 2: Enhanced Features (3 months)

**Month 4: Voice & Optimization**
- Amazon Transcribe integration
- Voice context extraction
- Route optimization with OR-Tools
- Navigation integration

**Month 5: Validation & Prediction**
- Before-after validation model training
- Semantic segmentation implementation
- Basic epidemic prediction model
- Hotspot detection algorithm

**Month 6: Refinement & Expansion**
- Multi-language support
- Offline capability enhancement
- Performance optimization
- Expand to 3 wards

**Deliverables:**
- Voice note support
- Route optimization (30% fuel savings)
- Anti-fraud validation (90%+ accuracy)
- 1,000+ active users

### Phase 3: Scale & Integration (6 months)

**Month 7-9: Advanced Features**
- Advanced epidemic prediction
- Integration with municipal ERP
- Advanced analytics and reporting
- Mobile app optimization

**Month 10-12: City-Wide Rollout**
- Infrastructure scaling
- Load testing (10,000+ concurrent users)
- Training programs for workers
- Marketing and awareness campaigns
- City-wide deployment

**Deliverables:**
- City-wide coverage
- 10,000+ active users
- Integration with government systems
- Measurable impact metrics

---

## 11. Cost Analysis

### 11.1 AWS Service Costs (Monthly Estimates)

**Assumptions:**
- 10,000 reports per month
- 500 active workers
- 50 authority users
- Average 2 photos per report
- 30% voice notes

| Service | Usage | Unit Cost | Monthly Cost (₹) |
|---------|-------|-----------|------------------|
| **Amazon S3** | 50GB storage, 20,000 requests | ₹1.84/GB, ₹0.37/1000 req | ₹100 |
| **Amazon RDS** | db.t3.medium, 100GB | ₹0.017/hour | ₹12,240 |
| **AWS Lambda** | 100,000 invocations, 512MB | ₹0.20/1M requests | ₹20 |
| **Amazon Rekognition** | 10,000 images | ₹10/1000 images | ₹1,000 |
| **Amazon Transcribe** | 3,000 minutes | ₹2.4/hour | ₹1,200 |
| **Amazon Comprehend** | 30,000 units | ₹0.10/100 units | ₹300 |
| **API Gateway** | 200,000 requests | ₹0.35/1M requests | ₹7 |
| **ElastiCache** | cache.t3.micro | ₹0.017/hour | ₹1,224 |
| **CloudWatch** | Logs, metrics | ₹0.50/GB | ₹200 |
| **Data Transfer** | 100GB out | ₹7.5/GB | ₹750 |
| **SageMaker** | ml.t3.medium, 100 hours | ₹5/hour | ₹500 |
| **EC2 (Route Opt)** | t3.medium, 24/7 | ₹0.042/hour | ₹3,024 |
| **Backup & Misc** | - | - | ₹500 |
| **TOTAL** | | | **₹21,065** |

**Per Ticket Cost:** ₹21,065 / 10,000 = **₹2.10 per ticket**

### 11.2 Cost Optimization Strategies

1. **S3 Lifecycle Policies:**
   - Move to S3 Glacier after 90 days: Save 80%
   - Delete after 1 year: Further savings

2. **Lambda Optimization:**
   - Use ARM-based Graviton processors: 20% cheaper
   - Optimize memory allocation: Reduce costs

3. **RDS Reserved Instances:**
   - 1-year commitment: 30% discount
   - 3-year commitment: 50% discount

4. **Spot Instances for ML Training:**
   - Use EC2 Spot for model training: 70% cheaper
   - SageMaker Spot training: 90% cheaper

5. **Caching Strategy:**
   - Cache dashboard queries: Reduce RDS load
   - CDN for static assets: Reduce data transfer

**Optimized Monthly Cost:** ₹12,000 - ₹15,000  
**Optimized Per Ticket Cost:** ₹1.20 - ₹1.50

### 11.3 Scaling Costs

| Scale | Reports/Month | Monthly Cost (₹) | Per Ticket (₹) |
|-------|---------------|------------------|----------------|
| Pilot (1 ward) | 1,000 | ₹8,000 | ₹8.00 |
| Small (3 wards) | 10,000 | ₹15,000 | ₹1.50 |
| Medium (City zone) | 50,000 | ₹45,000 | ₹0.90 |
| Large (Full city) | 200,000 | ₹120,000 | ₹0.60 |

**Economies of Scale:** Cost per ticket decreases as volume increases

### 11.4 ROI Analysis

**Municipal Savings:**
1. **Fuel Savings:** 30% reduction
   - Average fuel cost: ₹50,000/month per ward
   - Savings: ₹15,000/month per ward

2. **Labor Efficiency:** 40% time savings
   - Reduced overtime costs
   - Better resource allocation

3. **Disease Prevention:**
   - Reduced healthcare costs
   - Fewer epidemic response expenses

**Break-Even:** 2-3 months for pilot ward

---

## 12. Monitoring & Maintenance

### 12.1 Monitoring Strategy

**CloudWatch Metrics:**
- API response times (p50, p95, p99)
- Lambda execution duration and errors
- RDS CPU and memory utilization
- S3 request rates
- Custom metrics: Reports per hour, spam rate, validation accuracy

**Alarms:**
- API error rate > 5%
- Lambda timeout rate > 2%
- RDS CPU > 80%
- Disk space < 20%
- High-priority report pending > 2 hours

**Dashboards:**
- Real-time system health
- Business metrics (reports, completions)
- Cost tracking
- User activity

### 12.2 Logging Strategy

**Log Aggregation:**
- All Lambda logs to CloudWatch Logs
- Structured logging (JSON format)
- Log retention: 30 days (hot), 1 year (cold)

**Log Analysis:**
- CloudWatch Insights for queries
- Error pattern detection
- Performance bottleneck identification

### 12.3 Maintenance Plan

**Daily:**
- Monitor system health
- Review high-priority alerts
- Check spam detection accuracy

**Weekly:**
- Review performance metrics
- Analyze user feedback
- Update ML models with new data

**Monthly:**
- Security audit
- Cost optimization review
- Capacity planning
- Feature prioritization

**Quarterly:**
- Disaster recovery drill
- Penetration testing
- User satisfaction survey
- Strategic planning

---

## 13. Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| AWS service outage | Multi-AZ deployment, automated failover |
| Data loss | Daily backups, point-in-time recovery |
| Security breach | Encryption, regular audits, penetration testing |
| ML model drift | Continuous monitoring, retraining pipeline |
| Scalability issues | Auto-scaling, load testing, performance optimization |
| User adoption | User training, simple UI, community engagement |

---

## Conclusion

SanitiSense AI is designed as a scalable, cost-effective, and impactful solution that bridges the gap between citizens and civic systems. The architecture leverages AWS managed services for reliability and cost optimization, while the AI/ML pipeline ensures accurate and efficient processing of citizen reports.

**For the Hackathon:** We will deliver a functional prototype demonstrating the core workflow, complete technical documentation, and a compelling vision for scale. The prototype will showcase the feasibility of our Triple-Lock Mechanism and validate our approach with judges and potential stakeholders.

**Post-Hackathon:** The phased implementation approach allows for iterative development and validation, minimizing risks while maximizing impact. Each phase builds upon the previous one, with clear milestones and measurable outcomes. With a focus on inclusivity, accountability, and disease prevention, SanitiSense AI has the potential to transform urban sanitation management in India.

**Timeline Summary:**
- **Hackathon (Weeks 1-3):** Prototype + Documentation
- **Phase 1 (Months 1-3):** Production MVP with single ward pilot
- **Phase 2 (Months 4-6):** Enhanced features with 3-ward expansion
- **Phase 3 (Months 7-12):** City-wide scale with advanced capabilities

This realistic yet ambitious roadmap demonstrates our commitment to building a sustainable solution that creates lasting impact for underserved communities across India.
