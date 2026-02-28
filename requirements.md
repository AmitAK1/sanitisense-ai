# SanitiSense AI - Requirements Document

## Project Information

**Team Name:** Swadeshi Coders  
**Team Leader:** Amit Anil Kamble  
**Challenge Track:** [Student Track] AI for Communities, Access & Public Impact  
**Problem Statement:** Build an AI-powered solution that improves access to information, resources, or opportunities for communities and public systems.

---

## Quick Reference

| Aspect | Detail |
|--------|--------|
| **Core Innovation** | Triple-Lock Mechanism: AI Verification (Bedrock) + Route Optimization + Epidemic Prediction (RAG) |
| **Target Users** | 3 stakeholders: Citizens (reporters), Workers (field operators), Authorities (decision-makers) |
| **Languages Supported** | 7 Indian languages covering 80%+ population (Hindi, English, Marathi, Tamil, Telugu, Bengali, Gujarati) |
| **Generative AI** | Amazon Bedrock (Claude 3 Sonnet — Vision + Text), Bedrock Knowledge Base + Titan Embeddings (RAG) |
| **Key Impact Metrics** | 30% fuel savings, 40% time savings, 90%+ validation accuracy, 50% reduction in repeat complaints |
| **Implementation Timeline** | 3-week prototype → 3-month MVP → 12-month city-wide rollout |
| **Cost Efficiency** | ₹1.20-₹1.50 per resolved ticket (optimized), 2-3 month break-even for pilot ward |
| **Accessibility** | Zero-literacy design, offline-capable, works on low-end devices (2GB RAM, Android 8.0+) |
| **AWS Services** | Bedrock, Lambda, API Gateway, DynamoDB, S3, Amplify, Rekognition, Transcribe, CloudWatch |
| **AI Accuracy Targets** | 95%+ spam detection, 85%+ severity classification, 90%+ cleanup validation |

---

## Executive Summary

SanitiSense AI is not just a reporting tool; it is a **Civic Operating System** that creates a closed-loop ecosystem connecting three key stakeholders:
- **Citizens** (via inclusive, literacy-barrier-free reporting)
- **Sanitation Workers** (via dynamic route optimization and task management)
- **Municipal Authorities** (via epidemic prediction and evidence-backed dashboards)

**Core Philosophy:** "We don't just identify the trash; we ensure it leaves the street and prevent it from coming back."

### Why Now?

This solution is timely and relevant due to several converging factors:

1. **Post-COVID Public Health Focus**
   - Heightened awareness of sanitation's role in disease prevention
   - Government emphasis on proactive health measures
   - Community demand for better civic services

2. **Swachh Bharat Mission 2.0 (2021-2026)**
   - National focus on urban sanitation
   - Budget allocation for innovative solutions
   - Municipal willingness to adopt technology

3. **Digital India Initiative**
   - Smartphone penetration in underserved communities (60%+)
   - Improved 4G/5G connectivity in urban areas
   - Government push for digital civic services

4. **AI/ML Technology Maturity**
   - Amazon Bedrock provides foundation models (Claude 3 Sonnet) with vision + text capabilities
   - RAG workflows (Bedrock Knowledge Base + Titan Embeddings) enable grounded epidemic predictions
   - AWS AI services (Rekognition, Transcribe) now support Indian languages
   - Cost-effective cloud infrastructure
   - Proven success of AI in civic tech globally

5. **Funding Ecosystem**
   - Growing interest from impact investors in civic tech
   - Government grants for sanitation innovation
   - NGO partnerships for pilot programs

---

## Problem Statement

### Current Challenges

1. **The Literacy Wall**
   - Existing civic apps (e.g., Swachhata) are built for the literate elite, not for people living in underserved communities
   - Complex text inputs and English/Hindi menus exclude daily wage workers and slum residents
   - These communities abandon apps immediately due to navigation complexity

2. **The Invisible Crisis**
   - Communities that cannot log formal tickets are assumed to be "clean" by administration
   - The city's most dangerous sanitation hotspots remain completely off the municipal radar
   - Lack of evidence-based reporting leads to ignored complaints

3. **Inefficient Municipal Operations**
   - No prioritization mechanism for sanitation complaints
   - Workers waste time on false alarms and spam reports
   - No accountability mechanism to verify actual cleanup
   - Reactive approach instead of proactive disease prevention

4. **Systemic Gaps**
   - Municipal systems prioritize formal, written, categorized grievances
   - Unstructured photo and voice-based reports are ignored or rejected
   - No aggregation of repeated complaints to identify critical zones
   - Lack of correlation between sanitation hazards and health risks

---

## Solution Overview

SanitiSense AI acts as an **intelligent translation layer** between citizen reality and municipal systems, transforming informal reports into structured, actionable civic data.

### The Triple-Lock Mechanism (Core USP)

1. **AI Verification** - Validates reports and filters spam automatically
2. **Route Optimization** - Executes cleanup efficiently ("Uber for Garbage")
3. **Epidemic Forecasting** - Predicts health risks before outbreaks occur

---

## Stakeholder Analysis

### Primary Users

#### 1. Citizens (Reporters)
**Profile:**
- Low-literacy or illiterate residents
- Daily wage workers, slum dwellers
- Limited smartphone experience
- Prefer vernacular languages
- Intermittent internet connectivity

**Needs:**
- Simple, photo-first interface
- Voice-based context input
- Offline capability
- No complex forms or text entry
- Immediate acknowledgment of reports

#### 2. Sanitation Workers (Field Operators)
**Profile:**
- Municipal or contracted workers
- Basic smartphone literacy
- Need turn-by-turn navigation
- Accountable for task completion
- Work in teams with assigned vehicles

**Needs:**
- Clear task prioritization
- Optimized daily routes
- Navigation to exact problem locations
- Simple proof-of-work mechanism
- Offline task viewing capability

#### 3. Municipal Authorities & Health Officials
**Profile:**
- Ward officers, health department officials
- NGO coordinators
- Decision-makers for resource allocation
- Need data-driven insights

**Needs:**
- Real-time sanitation hazard dashboard
- Severity-based issue prioritization
- Hotspot identification
- Epidemic risk prediction
- Evidence-backed reporting
- Performance metrics and analytics

---

## Functional Requirements

### FR1: Citizen Reporting Module

#### FR1.1: Photo-Based Issue Submission
- **Priority:** Critical
- **Description:** Citizens must be able to capture and submit photos of sanitation issues
- **Acceptance Criteria:**
  - Camera interface opens with single tap
  - Photo captured with GPS coordinates and timestamp
  - Works offline; queues for upload when online
  - Maximum photo size: 5MB (auto-compressed)
  - Supports multiple photos per report (up to 3)

#### FR1.2: Voice-Based Context Capture
- **Priority:** High
- **Description:** Optional voice note to provide contextual information
- **Acceptance Criteria:**
  - Voice recording up to 60 seconds
  - Supports 7 major Indian languages: Hindi, English, Marathi, Tamil, Telugu, Bengali, Gujarati
  - Works offline; queues for upload
  - Visual feedback during recording
  - Playback option before submission

#### FR1.3: Minimal Text Input
- **Priority:** Medium
- **Description:** Optional location name or landmark (voice-to-text enabled)
- **Acceptance Criteria:**
  - Voice-to-text conversion for location input
  - Auto-suggest nearby landmarks using GPS
  - Maximum 50 characters
  - Completely optional field

#### FR1.4: Submission Confirmation
- **Priority:** High
- **Description:** Immediate acknowledgment with unique ticket ID
- **Acceptance Criteria:**
  - Generate unique 6-digit ticket ID
  - Display confirmation screen with ticket number
  - SMS notification with ticket ID (if phone number provided)
  - Ability to track ticket status

### FR2: AI Verification & Classification Module

#### FR2.1: Image Validation
- **Priority:** Critical
- **Description:** Automatically verify if image represents a genuine sanitation hazard
- **Acceptance Criteria:**
  - Classify image into categories: garbage pile, overflowing drain, blocked sewer, animal carcass, medical waste, other
  - Reject spam images (selfies, unrelated content) with 95%+ accuracy
  - Detect image quality issues (too dark, blurry)
  - Processing time: < 3 seconds per image

#### FR2.2: Severity Scoring
- **Priority:** Critical
- **Description:** Estimate severity level based on visual cues
- **Acceptance Criteria:**
  - Three severity levels: High (bio-hazard, blocked roads), Medium (large accumulation), Low (minor litter)
  - Consider factors: size/spread, obstruction level, proximity to water bodies
  - Severity score: 1-10 scale
  - 85%+ accuracy compared to manual expert assessment

#### FR2.3: Voice Context Extraction
- **Priority:** High
- **Description:** Extract urgency indicators from voice notes
- **Acceptance Criteria:**
  - Transcribe voice to text with 90%+ accuracy
  - Identify urgency keywords: "smell", "days/weeks", "children playing", "water mixed", "blocking road"
  - Adjust severity score based on voice context (+/- 2 points)
  - Support code-mixed language (Hindi-English, etc.)

#### FR2.4: Duplicate Detection
- **Priority:** High
- **Description:** Identify and cluster duplicate reports for same issue
- **Acceptance Criteria:**
  - Detect reports within 50-meter radius
  - Group reports submitted within 7 days
  - Increase priority for repeated complaints
  - Show "X people reported this" on dashboard

### FR3: Route Optimization Module ("Uber for Garbage")

#### FR3.1: Dynamic Route Generation
- **Priority:** Critical
- **Description:** Generate optimized daily pickup routes for sanitation vehicles
- **Acceptance Criteria:**
  - Consider vehicle capacity, working hours, traffic conditions
  - Prioritize high-severity issues
  - Minimize total travel distance and time
  - Support multiple vehicles/teams
  - Regenerate routes when new high-priority issues arrive

#### FR3.2: Turn-by-Turn Navigation
- **Priority:** High
- **Description:** Provide navigation to sanitation workers
- **Acceptance Criteria:**
  - Integration with Google Maps SDK
  - Voice-guided navigation in local language
  - Show next 3 tasks in queue
  - Display estimated time to reach location
  - Offline map support for assigned routes

#### FR3.3: Task Management
- **Priority:** High
- **Description:** Workers can view, accept, and complete tasks
- **Acceptance Criteria:**
  - List view of assigned tasks with priority indicators
  - "Start Task" button to begin navigation
  - "Mark Complete" requires photo upload
  - Ability to report issues (location incorrect, already cleaned, etc.)

### FR4: Anti-Fraud "Proof of Cleanliness" Module

#### FR4.1: Before-After Photo Comparison
- **Priority:** Critical
- **Description:** Workers must upload "After" photo to close ticket
- **Acceptance Criteria:**
  - Mandatory photo upload to mark task complete
  - AI compares "Before" vs "After" images
  - Verify same location using GPS (within 20-meter tolerance)
  - Verify waste pile is actually removed (not just different angle)
  - Rejection if validation fails; ticket remains open

#### FR4.2: Validation Algorithm
- **Priority:** Critical
- **Description:** AI validates actual cleanup occurred
- **Acceptance Criteria:**
  - Use semantic segmentation to identify waste in both images
  - Calculate waste reduction percentage
  - Minimum 70% waste reduction required for approval
  - Flag suspicious submissions for manual review
  - 90%+ accuracy in detecting fake completions

#### FR4.3: Worker Performance Tracking
- **Priority:** Medium
- **Description:** Track completion rates and validation success
- **Acceptance Criteria:**
  - Dashboard showing completed vs rejected tasks per worker
  - Average time per task
  - Validation success rate
  - Leaderboard for motivation (optional)

### FR5: Epidemic Prediction Module

#### FR5.1: Hotspot Detection
- **Priority:** High
- **Description:** Identify areas with repeated sanitation issues
- **Acceptance Criteria:**
  - Spatial clustering algorithm (DBSCAN or similar)
  - Identify zones with 5+ reports in 30-day period
  - Visualize hotspots on heatmap
  - Rank hotspots by severity and frequency

#### FR5.2: Disease Risk Correlation
- **Priority:** High
- **Description:** Predict epidemic risk based on sanitation data
- **Acceptance Criteria:**
  - Correlate garbage accumulation with historical disease outbreak data
  - Identify high-risk zones for vector-borne diseases (Dengue, Malaria, Cholera)
  - Risk score: Low, Medium, High, Critical
  - Update risk scores daily
  - Alert health officials when risk exceeds threshold

#### FR5.3: Water Stagnation Integration
- **Priority:** Medium (Phase 2)
- **Description:** Enhance predictions with water stagnation data
- **Acceptance Criteria:**
  - Integrate with municipal water stagnation databases (if available)
  - Use satellite imagery APIs for water body detection (optional)
  - Correlate proximity to water bodies with disease risk
  - Increase risk score for issues near stagnant water

#### FR5.4: Predictive Alerts
- **Priority:** High
- **Description:** Proactive alerts to health department
- **Acceptance Criteria:**
  - Automated email/SMS alerts when risk level changes
  - Weekly risk assessment reports
  - Recommendations for preventive action
  - Historical trend analysis

### FR6: Monitoring Dashboard

#### FR6.1: Real-Time Issue Tracking
- **Priority:** Critical
- **Description:** Live dashboard for authorities
- **Acceptance Criteria:**
  - Map view with color-coded markers (red=high, yellow=medium, green=low)
  - Filter by severity, status, date range, ward/zone
  - Click marker to view issue details and photos
  - Real-time updates when new reports arrive

#### FR6.2: Analytics & Reporting
- **Priority:** High
- **Description:** Data-driven insights for decision-making
- **Acceptance Criteria:**
  - Total reports: daily, weekly, monthly
  - Resolution time: average and by severity
  - Hotspot trends over time
  - Worker performance metrics
  - Epidemic risk dashboard
  - Export reports as PDF/Excel

#### FR6.3: Evidence-Backed Verification
- **Priority:** High
- **Description:** View before-after photos for completed tasks
- **Acceptance Criteria:**
  - Side-by-side photo comparison
  - GPS coordinates and timestamps
  - AI validation score
  - Ability to reopen ticket if cleanup insufficient

---

## Non-Functional Requirements

### NFR1: Performance

- **Response Time:** 
  - Image upload: < 5 seconds on 3G connection
  - AI verification: < 3 seconds per image
  - Route generation: < 10 seconds for 50 tasks
  - Dashboard load time: < 2 seconds

- **Throughput:**
  - Support 10,000 concurrent users
  - Process 1,000 reports per hour
  - Handle 100 simultaneous route optimizations

- **Scalability:**
  - Horizontal scaling for increased load
  - Support city-wide deployment (1M+ population)

### NFR2: Availability & Reliability

- **Uptime:** 99.5% availability (excluding planned maintenance)
- **Data Backup:** Daily automated backups with 30-day retention
- **Disaster Recovery:** Recovery Time Objective (RTO) < 4 hours
- **Offline Capability:** Core citizen and worker features work offline

### NFR3: Security & Privacy

- **Data Encryption:** 
  - Data in transit: TLS 1.3
  - Data at rest: AES-256 encryption

- **Authentication:**
  - Citizens: Optional phone number (for tracking only)
  - Workers: Username/password + OTP
  - Authorities: Role-based access control (RBAC)

- **Privacy:**
  - No personal data collection from citizens (anonymous reporting)
  - GPS coordinates rounded to 10-meter precision (privacy protection)
  - Photos stored securely; access logged
  - GDPR/Data Protection Act compliance

### NFR4: Usability & Accessibility

- **Language Support:** 7 major Indian languages
  - Hindi, English, Marathi, Tamil, Telugu, Bengali, Gujarati
  - Covers 80%+ of Indian population
- **Literacy Level:** Designed for zero-literacy users
- **Interface:** 
  - Large buttons (minimum 48x48 dp)
  - High contrast colors
  - Icon-based navigation
  - Voice feedback for actions

- **Device Compatibility:**
  - Android 8.0+ (95% device coverage)
  - iOS 12+ (optional Phase 2)
  - Works on low-end devices (2GB RAM)

### NFR5: Maintainability

- **Code Quality:** 80%+ test coverage
- **Documentation:** API documentation, deployment guides
- **Monitoring:** Real-time error tracking and logging
- **Updates:** Over-the-air (OTA) updates for mobile apps

### NFR6: Compliance

- **Standards:** 
  - ISO 27001 (Information Security)
  - WCAG 2.1 Level AA (Accessibility)
  
- **Legal:**
  - Data Protection Act compliance
  - Municipal data sharing agreements
  - Worker consent for performance tracking

---

## User Stories

### Citizen User Stories

**US1:** As a slum resident, I want to report a garbage pile using just a photo, so that I don't need to fill complex forms.

**US2:** As a non-English speaker, I want to describe the problem in my local language using voice, so that authorities understand the urgency.

**US3:** As a citizen with poor internet, I want to submit reports offline, so that connectivity doesn't prevent me from reporting issues.

**US4:** As a concerned resident, I want to track my complaint status, so that I know if action has been taken.

**US5:** As a community member, I want to see if others have reported the same issue, so that I know it's being prioritized.

### Sanitation Worker User Stories

**US6:** As a sanitation worker, I want to see my daily tasks on a map, so that I can plan my work efficiently.

**US7:** As a driver, I want turn-by-turn navigation to problem locations, so that I don't waste time searching.

**US8:** As a field worker, I want to upload proof of cleanup, so that my work is acknowledged and tickets are closed.

**US9:** As a team member, I want to see task priorities, so that I handle urgent issues first.

**US10:** As a worker, I want to access my task list offline, so that I can work even without internet.

### Authority User Stories

**US11:** As a ward officer, I want to see all sanitation issues on a map, so that I can allocate resources effectively.

**US12:** As a health official, I want to identify disease risk zones, so that I can take preventive action before outbreaks.

**US13:** As a municipal administrator, I want to track worker performance, so that I can ensure accountability.

**US14:** As a decision-maker, I want to see trends and analytics, so that I can plan long-term improvements.

**US15:** As an authority, I want evidence-backed reports, so that I can verify actual cleanup occurred.

---

## Success Metrics

### Impact Metrics

1. **Increased Acknowledgment:** 80%+ of valid complaints acknowledged within 24 hours
2. **Faster Response:** Average resolution time reduced by 40%
3. **Reduced Repeat Complaints:** 50% reduction in duplicate reports from same areas
4. **Improved Accountability:** 90%+ task completion with verified proof

### Operational Metrics

1. **Fuel Savings:** 30% reduction in municipal fuel costs via route optimization
2. **Labor Efficiency:** 40% reduction in time wasted on false alarms
3. **Spam Reduction:** 95%+ spam/invalid reports filtered automatically

### Social Impact Metrics

1. **Inclusion:** 100% accessible to illiterate population
2. **Disease Prevention:** Proactive removal of bio-hazards in high-risk zones
3. **Community Trust:** Increased citizen engagement with civic systems

### Technical Metrics

1. **AI Accuracy:** 95%+ for spam detection, 85%+ for severity classification
2. **System Uptime:** 99.5% availability
3. **User Adoption:** 10,000+ active users within 6 months of pilot

---

## Constraints & Assumptions

### Constraints

1. **Budget:** Cost-effective solution suitable for NGO pilots or ward-level rollouts
2. **Infrastructure:** Must work on low-end Android devices with intermittent 2G/3G connectivity
3. **Timeline:** MVP development within 3-4 months
4. **Resources:** Small development team (4-6 developers)

### Assumptions

1. **Device Access:** Target users have access to smartphones with cameras
2. **Municipal Cooperation:** Authorities willing to integrate system with existing workflows
3. **Worker Adoption:** Sanitation workers willing to use smartphone app for task management
4. **Data Availability:** Historical disease outbreak data available from health departments
5. **Network Coverage:** Minimum 2G connectivity available in target areas (even if intermittent)

---

## Out of Scope (Phase 2+)

1. Integration with existing municipal ERP systems
2. Payment/incentive system for citizens or workers
3. Advanced satellite imagery analysis for water stagnation
4. Predictive maintenance for sanitation infrastructure
5. Multi-city deployment and customization
6. iOS application (Phase 2 consideration)
7. Web-based citizen reporting portal
8. Integration with social media platforms (WhatsApp, Twitter)

---

## Dependencies

### External Dependencies

1. **AWS Services:** Rekognition, Transcribe, Lambda, S3, RDS
2. **Google Services:** Maps SDK, OR-Tools
3. **Third-Party APIs:** 
   - Weather data (optional)
   - Traffic data for route optimization
4. **Municipal Data:** Historical disease outbreak data, ward boundaries

### Internal Dependencies

1. **ML Models:** Pre-trained models for sanitation image classification
2. **Language Models:** Multi-lingual speech-to-text models
3. **Geospatial Data:** City maps, landmark databases

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Low user adoption due to digital literacy | High | Medium | Extensive user testing with target demographic; icon-based UI; community training |
| Poor AI accuracy on diverse sanitation issues | High | Medium | Continuous model training with local data; human-in-the-loop for edge cases |
| Worker resistance to accountability system | Medium | Medium | Incentive programs; transparent performance metrics; worker feedback integration |
| Insufficient municipal cooperation | High | Low | Pilot with progressive NGOs first; demonstrate ROI with data |
| Offline sync conflicts | Medium | Medium | Robust conflict resolution; timestamp-based priority |
| Privacy concerns with photo uploads | Medium | Low | Anonymous reporting; GPS rounding; clear privacy policy |
| Scalability issues during city-wide rollout | High | Low | Cloud-based architecture; load testing; phased rollout |
