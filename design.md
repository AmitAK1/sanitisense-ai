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
| **Frontend** | Flutter (Citizen & Worker apps), React (Authority dashboard) |
| **AI/ML Services** | Amazon Rekognition, Transcribe, Comprehend, Custom TensorFlow models |
| **Database** | PostgreSQL 14 with PostGIS extension for spatial queries |
| **Key AWS Services** | S3, RDS, Lambda, Rekognition, Transcribe, SageMaker, API Gateway, ElastiCache |
| **Cost (Optimized)** | ₹1.20-₹1.50 per ticket, ₹15,000/month for 10,000 tickets |
| **Scalability** | Supports 10,000 concurrent users, 1M+ population city-wide |
| **Security** | TLS 1.3, AES-256 encryption, RBAC, GDPR compliant |
| **Offline Support** | Full offline capability for citizen and worker apps with background sync |

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
│  Citizen App │   Worker App     │  Authority Dashboard    │
│  (Flutter)   │   (Flutter)      │  (React Web)            │
└──────────────┴──────────────────┴─────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                       │
│                    (AWS API Gateway)                         │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                       │
├──────────────┬──────────────────┬─────────────────────────┤
│ Report       │  Route           │  Analytics              │
│ Processing   │  Optimization    │  & Prediction           │
│ Service      │  Service         │  Service                │
│ (Lambda)     │  (Lambda/EC2)    │  (Lambda/SageMaker)     │
└──────────────┴──────────────────┴─────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI/ML SERVICES LAYER                      │
├──────────────┬──────────────────┬─────────────────────────┤
│ Image        │  Voice           │  Validation             │
│ Classification│ Transcription   │  & Comparison           │
│ (Rekognition)│ (Transcribe)     │  (Custom ML)            │
└──────────────┴──────────────────┴─────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
├──────────────┬──────────────────┬─────────────────────────┤
│ Relational   │  Object Storage  │  Cache                  │
│ Database     │  (Images/Audio)  │  (Redis)                │
│ (RDS)        │  (S3)            │  (ElastiCache)          │
└──────────────┴──────────────────┴─────────────────────────┘
```

### 1.2 Architecture Principles

1. **Microservices:** Loosely coupled services for independent scaling
2. **Serverless-First:** Use AWS Lambda for cost optimization
3. **Offline-First:** Mobile apps work without internet; sync when available
4. **Event-Driven:** Asynchronous processing using message queues
5. **Cloud-Native:** Leverage managed AWS services for reliability

### 1.3 Data Flow

#### Citizen Report Submission Flow
```
1. Citizen captures photo → 2. App stores locally (offline)
3. When online, upload to S3 → 4. Trigger Lambda function
5. Rekognition analyzes image → 6. Transcribe processes voice
7. NLP extracts context → 8. Severity scoring algorithm
9. Store in RDS → 10. Notify authorities → 11. Update dashboard
```

#### Worker Task Completion Flow
```
1. Worker views assigned task → 2. Navigates to location
3. Completes cleanup → 4. Uploads "After" photo to S3
5. Trigger validation Lambda → 6. Retrieve "Before" photo from report
7. AI comparison (semantic segmentation) → 8. Calculate waste reduction %
9. If valid (>70% reduction) → Mark complete → Update dashboard → Close ticket
10. If invalid → Reject → Notify worker → Keep ticket open → Request re-cleanup
```

---

## 2. Component Design

### 2.1 Citizen Mobile Application

**Technology:** Flutter (Dart)  
**Target Platforms:** Android 8.0+  
**Key Features:** Offline-first, camera integration, voice recording

#### Architecture Pattern: BLoC (Business Logic Component)

**Modules:**
- **Camera Module:** Native camera integration with compression
- **Voice Recorder:** Audio recording with format conversion (AAC/MP3)
- **Offline Storage:** SQLite for local data persistence
- **Sync Manager:** Background sync when connectivity available
- **Location Service:** GPS coordinates with fallback to network location

**UI Screens:**
1. Home Screen: Single large "Report Issue" button with camera icon
2. Camera Screen: Full-screen camera with capture button
3. Voice Note Screen: Record/stop/play controls with waveform visualization
4. Confirmation Screen: Ticket ID display with status tracking option
5. Track Status Screen: Simple list of submitted reports

**Offline Capability:**
- Store photos in local app directory (max 10 pending reports)
- Queue metadata in SQLite
- Background service checks connectivity every 5 minutes
- Upload in order of severity (high priority first)
- Show sync status indicator

### 2.2 Worker Mobile Application

**Technology:** Flutter (Dart)  
**Target Platforms:** Android 8.0+  
**Key Features:** Map integration, navigation, task management

**Modules:**
- **Map Module:** Google Maps SDK integration
- **Navigation Module:** Turn-by-turn directions with voice guidance
- **Task Manager:** View, accept, complete tasks
- **Camera Module:** Before/after photo capture
- **Offline Maps:** Download assigned route areas

**UI Screens:**
1. Login Screen: Username/password + OTP verification
2. Task List Screen: Prioritized list with severity indicators
3. Map View Screen: All assigned tasks on map (Uber-like interface)
4. Navigation Screen: Active navigation with next task preview
5. Task Detail Screen: Issue photos, location, description
6. Completion Screen: Upload "After" photo with validation feedback
7. Performance Dashboard: Personal stats and leaderboard

### 2.3 Authority Web Dashboard

**Technology:** React.js + Material-UI  
**Target Platforms:** Web browsers (Chrome, Firefox, Safari)  
**Key Features:** Real-time monitoring, analytics, reporting

**Modules:**
- **Map Visualization:** Interactive map with clustered markers
- **Analytics Engine:** Charts and graphs using Chart.js/D3.js
- **Report Generator:** PDF/Excel export functionality
- **Alert System:** Real-time notifications for high-priority issues
- **User Management:** RBAC for different authority levels

**UI Sections:**
1. Dashboard Home: Key metrics, active issues, recent completions
2. Map View: Interactive map with filters and search
3. Analytics: Trends, hotspots, performance metrics
4. Epidemic Risk: Heatmap with risk zones and predictions
5. Reports: Generate and download custom reports
6. Settings: User management, system configuration

---

## 3. Technology Stack

### 3.1 Frontend Technologies

| Component | Technology | Justification |
|-----------|------------|---------------|
| Citizen App | Flutter 3.x | Cross-platform, offline-first, native performance |
| Worker App | Flutter 3.x | Consistent UX, code reuse, map integration |
| Dashboard | React 18 + TypeScript | Rich ecosystem, real-time updates, component reusability |
| UI Framework | Material Design 3 | Accessibility, familiar patterns, responsive |
| State Management | BLoC (Flutter), Redux (React) | Predictable state, testability |
| Maps | Google Maps SDK | Reliable, offline support, navigation |

### 3.2 Backend Technologies

| Component | Technology | Justification |
|-----------|------------|---------------|
| API Gateway | AWS API Gateway | Managed service, auto-scaling, request throttling |
| Compute | AWS Lambda (Node.js 18) | Serverless, pay-per-use, auto-scaling |
| Heavy Compute | AWS EC2 (t3.medium) | Route optimization, batch processing |
| Database | Amazon RDS (PostgreSQL 14) | ACID compliance, spatial queries (PostGIS) |
| Cache | Amazon ElastiCache (Redis) | Fast reads, session management |
| Object Storage | Amazon S3 | Scalable, durable, lifecycle policies |
| Message Queue | Amazon SQS | Asynchronous processing, decoupling |

### 3.3 AI/ML Technologies

| Component | Technology | Justification |
|-----------|------------|---------------|
| Image Classification | Amazon Rekognition Custom Labels | Pre-trained models, easy training, managed |
| Speech-to-Text | Amazon Transcribe | Multi-language, custom vocabulary |
| NLP | AWS Comprehend | Sentiment analysis, entity extraction |
| Custom ML | TensorFlow 2.x / PyTorch | Semantic segmentation, before/after comparison |
| ML Training | Amazon SageMaker | Managed training, model versioning |
| ML Inference | Lambda + SageMaker Endpoint | Low latency, cost-effective |

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
| Route Optimization | Google OR-Tools | Open source, VRP solver, Python library |
| Spatial Analysis | PostGIS (PostgreSQL extension) | Geospatial queries, clustering |
| Analytics | Amazon QuickSight (optional) | BI dashboards, data visualization |
| Data Pipeline | AWS Glue (optional Phase 2) | ETL, data transformation |

---

## 4. AWS Services Architecture

### 4.1 Core AWS Services

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

#### Amazon RDS (Relational Database Service)
**Purpose:** Store structured data (tickets, users, tasks, analytics)

**Instance Type:** db.t3.medium (2 vCPU, 4GB RAM)  
**Engine:** PostgreSQL 14 with PostGIS extension  
**Storage:** 100GB SSD with auto-scaling to 500GB  
**Backup:** Automated daily backups, 7-day retention

**Database Schema:** (See Section 5)

#### AWS Lambda
**Purpose:** Serverless compute for API endpoints and event processing

**Functions:**
1. `report-processor`: Process new citizen reports
2. `image-classifier`: Trigger Rekognition and classify images
3. `voice-transcriber`: Trigger Transcribe and extract context
4. `severity-scorer`: Calculate severity based on AI outputs
5. `route-optimizer`: Generate daily routes (scheduled)
6. `validation-checker`: Validate worker completion photos
7. `epidemic-predictor`: Calculate disease risk scores (scheduled)
8. `notification-sender`: Send alerts to authorities

**Configuration:**
- Runtime: Node.js 18
- Memory: 512MB - 2GB (based on function)
- Timeout: 30 seconds (API), 15 minutes (batch)
- Concurrency: 100 concurrent executions

#### Amazon Rekognition
**Purpose:** Image classification and object detection

**Custom Labels Model:**
- Training dataset: 5,000+ labeled images per category
- Categories: garbage_pile, overflowing_drain, blocked_sewer, animal_carcass, medical_waste, spam
- Confidence threshold: 85%
- Inference: Real-time via Lambda

**Features Used:**
- Custom Labels: Sanitation issue classification
- Object Detection: Identify waste objects
- Image Moderation: Filter inappropriate content

#### Amazon Transcribe
**Purpose:** Convert voice notes to text

**Configuration:**
- Languages: Hindi (hi-IN), English (en-IN), Marathi (mr-IN), Tamil (ta-IN), Telugu (te-IN), Bengali (bn-IN), Gujarati (gu-IN)
- Custom vocabulary: Sanitation-related terms (e.g., "kachra", "gutter", "naala")
- Output format: JSON with timestamps
- Speaker identification: Disabled (single speaker)

#### Amazon Comprehend
**Purpose:** Extract urgency indicators from transcribed text

**Features Used:**
- Sentiment Analysis: Detect urgency/frustration
- Key Phrase Extraction: Identify important context
- Entity Recognition: Extract locations, durations

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

#### Amazon SQS (Simple Queue Service)
**Purpose:** Asynchronous task processing

**Queues:**
1. `report-processing-queue`: New reports for AI analysis
2. `notification-queue`: Alerts to send
3. `route-optimization-queue`: Daily route generation requests
4. `validation-queue`: Worker completion validations

**Configuration:**
- Visibility timeout: 5 minutes
- Message retention: 4 days
- Dead letter queue: For failed messages

#### Amazon ElastiCache (Redis)
**Purpose:** Caching and session management

**Use Cases:**
- Cache dashboard statistics (5-minute TTL)
- Store active worker sessions
- Rate limiting for API endpoints
- Temporary storage for route optimization results

**Configuration:**
- Node type: cache.t3.micro
- Cluster mode: Disabled (single node for MVP)
- Eviction policy: LRU (Least Recently Used)

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

### 7.1 Image Classification Pipeline

**Objective:** Classify sanitation issues and detect spam

**Architecture:**
```
Input Image → Preprocessing → Rekognition Custom Labels → 
Post-processing → Severity Estimation → Store Results
```

**Model Training:**
1. **Dataset Collection:**
   - 5,000+ images per category
   - Categories: garbage_pile, overflowing_drain, blocked_sewer, animal_carcass, medical_waste, spam
   - Crowdsourced from municipal workers and online datasets

2. **Data Augmentation:**
   - Rotation, flip, brightness adjustment
   - Simulate different lighting conditions
   - Add noise for robustness

3. **Training Process:**
   - Use Amazon Rekognition Custom Labels
   - Train/validation split: 80/20
   - Target accuracy: 90%+
   - Iterative improvement with production data

**Inference:**
- Lambda function triggers Rekognition API
- Response time: < 2 seconds
- Confidence threshold: 85%
- Fallback: Manual review queue for low confidence

**Severity Estimation Algorithm:**
```python
def calculate_severity(category, bounding_boxes, image_metadata):
    base_severity = CATEGORY_SEVERITY_MAP[category]
    
    # Factor 1: Size of waste (from bounding boxes)
    total_area = sum([box.width * box.height for box in bounding_boxes])
    size_factor = min(total_area / image_area, 1.0) * 3
    
    # Factor 2: Proximity to sensitive areas (from GPS)
    proximity_factor = check_proximity_to_schools_hospitals(gps_coords)
    
    # Factor 3: Obstruction level (heuristic)
    obstruction_factor = estimate_obstruction(bounding_boxes)
    
    severity = base_severity + size_factor + proximity_factor + obstruction_factor
    return min(max(severity, 1), 10)  # Clamp to 1-10
```

### 7.2 Voice Processing Pipeline

**Objective:** Transcribe voice notes and extract urgency indicators

**Architecture:**
```
Audio File → Format Conversion → Amazon Transcribe → 
Text Output → Amazon Comprehend → Urgency Score → Store Results
```

**Process:**
1. **Audio Preprocessing:**
   - Convert to supported format (MP3/WAV)
   - Normalize audio levels
   - Remove background noise (optional)

2. **Transcription:**
   - Amazon Transcribe with custom vocabulary
   - Supports 7 Indian languages: Hindi, English, Marathi, Tamil, Telugu, Bengali, Gujarati
   - Language auto-detection (if not specified by user)
   - Output: JSON with text and timestamps

3. **NLP Analysis:**
   - Extract key phrases using Comprehend
   - Identify urgency keywords in multiple languages: "smell"/"badbu", "days"/"din", "weeks"/"hafte", "children"/"bacche", "water"/"paani", "blocking"/"band"
   - Sentiment analysis for frustration level

4. **Urgency Scoring:**
```python
URGENCY_KEYWORDS = {
    "smell": 2, "stink": 2, "odor": 2,
    "days": 1, "weeks": 2, "months": 3,
    "children": 2, "school": 2,
    "water": 2, "drain": 1,
    "blocking": 2, "road": 1
}

def calculate_urgency_adjustment(transcript, sentiment):
    score = 0
    for keyword, weight in URGENCY_KEYWORDS.items():
        if keyword in transcript.lower():
            score += weight
    
    if sentiment == "NEGATIVE":
        score += 1
    
    return min(score, 3)  # Max +3 to severity
```

### 7.3 Before-After Validation Pipeline

**Objective:** Verify actual cleanup occurred

**Architecture:**
```
Before Image + After Image → Semantic Segmentation Model → 
Waste Detection → Area Calculation → Comparison → Validation Score
```

**Custom ML Model:**
- **Framework:** TensorFlow 2.x with DeepLab v3+ architecture
- **Training Data:** 10,000+ before-after image pairs
- **Output:** Pixel-wise segmentation mask (waste vs. background)

**Validation Algorithm:**
```python
def validate_cleanup(before_image, after_image, gps_before, gps_after):
    # Step 1: GPS proximity check
    distance = calculate_distance(gps_before, gps_after)
    if distance > 20:  # meters
        return {"valid": False, "reason": "Location mismatch"}
    
    # Step 2: Semantic segmentation
    before_mask = segmentation_model.predict(before_image)
    after_mask = segmentation_model.predict(after_image)
    
    # Step 3: Calculate waste area
    before_waste_pixels = np.sum(before_mask == WASTE_CLASS)
    after_waste_pixels = np.sum(after_mask == WASTE_CLASS)
    
    # Step 4: Calculate reduction percentage
    reduction = (before_waste_pixels - after_waste_pixels) / before_waste_pixels * 100
    
    # Step 5: Validation decision
    if reduction >= 70:
        return {"valid": True, "score": reduction, "status": "approved"}
    elif reduction >= 40:
        return {"valid": False, "score": reduction, "status": "partial", 
                "reason": "Incomplete cleanup"}
    else:
        return {"valid": False, "score": reduction, "status": "rejected",
                "reason": "Insufficient cleanup or fake photo"}
```

**Model Deployment:**
- Hosted on Amazon SageMaker Endpoint
- Instance type: ml.t3.medium
- Auto-scaling: 1-5 instances based on load
- Inference time: < 5 seconds per comparison

### 7.4 Epidemic Prediction Pipeline

**Objective:** Predict disease outbreak risk based on sanitation data

**Architecture:**
```
Historical Reports + Disease Data → Feature Engineering → 
ML Model (XGBoost) → Risk Score → Hotspot Identification → Alerts
```

**Features:**
1. **Spatial Features:**
   - Report density (reports per km²)
   - Proximity to water bodies
   - Proximity to residential areas
   - Elevation data

2. **Temporal Features:**
   - Days since last cleanup
   - Seasonal patterns (monsoon, summer)
   - Historical outbreak dates

3. **Sanitation Features:**
   - Average severity score
   - Category distribution (bio-hazards weighted higher)
   - Repeat complaint frequency

**Model:**
- **Algorithm:** XGBoost Classifier
- **Target:** Binary classification (outbreak risk: yes/no)
- **Training Data:** Historical sanitation + disease outbreak data (3-5 years)
- **Features:** 20+ engineered features
- **Evaluation Metric:** F1-score (balance precision and recall)

**Risk Scoring:**
```python
def calculate_disease_risk(location, radius=100):
    # Get reports in area
    reports = get_reports_in_radius(location, radius, days=30)
    
    # Feature extraction
    features = {
        'report_density': len(reports) / (math.pi * radius**2),
        'avg_severity': np.mean([r.severity for r in reports]),
        'bio_hazard_count': sum([1 for r in reports if r.category in BIO_HAZARDS]),
        'days_since_cleanup': min([r.days_pending for r in reports]),
        'proximity_to_water': get_water_proximity(location),
        'season': get_current_season(),
        'historical_outbreaks': get_outbreak_history(location)
    }
    
    # Model prediction
    risk_probability = epidemic_model.predict_proba(features)[0][1]
    
    # Risk level classification
    if risk_probability > 0.8:
        return {"level": "critical", "score": risk_probability * 100}
    elif risk_probability > 0.6:
        return {"level": "high", "score": risk_probability * 100}
    elif risk_probability > 0.4:
        return {"level": "medium", "score": risk_probability * 100}
    else:
        return {"level": "low", "score": risk_probability * 100}
```

**Scheduled Execution:**
- Run daily at 2 AM
- Update hotspot risk scores
- Send alerts for new high-risk zones
- Generate weekly risk reports

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
