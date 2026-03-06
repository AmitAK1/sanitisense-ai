"""
SanitiSense AI — Report Processor Lambda
POST /reports  — citizen submits a report
GET  /reports  — list all reports
GET  /reports/{ticket_id} — single report

IMPORTANT — this is synchronous (NOT async SQS).
The frontend waits for the AI result so it can show the citizen
their ticket ID + what kind of problem was detected.

Flow:
  1. Frontend already uploaded photo to S3 via GET /upload-url
  2. Frontend calls POST /reports { image_key, latitude, longitude }
  3. This Lambda calls Bedrock (via image_analyzer) to get REAL AI result
  4. If spam → reject with 400
  5. If real issue → save report + auto-create task → return ticket_id + ai_analysis

DynamoDB schema (must match the seeded 'SanitiSense' table):
  PK = REPORT#{ticket_id}   SK = META
"""

import json
import os
import uuid
from datetime import datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

# ── AWS clients ─────────────────────────────────────────────────────────────
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SanitiSense'))

S3_BUCKET = os.environ.get('S3_BUCKET', 'sanitisense-media-982253889131')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')


def generate_ticket_id() -> str:
    """
    Generate a unique ticket ID.
    Format: SAN + 6 uppercase hex chars  →  e.g. SAN4A2F1B
    """
    return f"SAN{uuid.uuid4().hex[:6].upper()}"


def _response(status_code: int, body: dict) -> dict:
    """Build a standard API Gateway response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, default=str),
    }


def _now() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def _priority_from_severity(severity: int) -> tuple:
    """Map severity score (1-10) to priority label and SLA hours."""
    if severity >= 8:
        return 'critical', 4
    elif severity >= 6:
        return 'high', 12
    elif severity >= 4:
        return 'medium', 24
    return 'low', 48


# ─────────────────────────────────────────────────────────────────────────────
# AI — call Bedrock directly (synchronous, same process)
# ─────────────────────────────────────────────────────────────────────────────

CLASSIFICATION_PROMPT = """Analyze this photo taken by a citizen reporting a sanitation issue in an Indian city.

Return ONLY a valid JSON object with exactly these fields:
{
  "is_spam": boolean,
  "category": "garbage_pile" | "overflowing_drain" | "blocked_sewer" | "stagnant_water" | "medical_waste" | "animal_carcass" | "other",
  "severity_score": integer 1-10,
  "description": "2-3 sentence human-readable description of the issue",
  "health_risk": "none" | "low" | "medium" | "high",
  "confidence": float 0.0-1.0
}

Severity guide:
- 1-3: Minor litter, small debris
- 4-6: Moderate accumulation, partial drain blockage
- 7-8: Large garbage piles, fully blocked drains, stagnant water
- 9-10: Bio-hazards, medical waste, dead animals, contaminated water near residences

If the image is NOT a sanitation issue (selfie, food, random photo), set is_spam=true and severity_score=0.
Return ONLY the JSON object, no other text."""


def analyze_image_from_s3(image_key: str) -> dict:
    """
    Pull image from S3, send to Bedrock Claude for classification.
    Returns the AI analysis dict.
    Falls back to smart keyword-based classification if Bedrock is unavailable.
    """
    import base64

    # Get image bytes from S3
    s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    response = s3.get_object(Bucket=S3_BUCKET, Key=image_key)
    image_bytes = response['Body'].read()

    # Detect media type from key extension
    ext = image_key.rsplit('.', 1)[-1].lower()
    media_type_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                      'png': 'image/png', 'webp': 'image/webp', 'heic': 'image/jpeg'}
    media_type = media_type_map.get(ext, 'image/jpeg')

    # Try Bedrock first, fall back to smart mock if unavailable
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 512,
            'messages': [{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {
                        'type': 'base64',
                        'media_type': media_type,
                        'data': image_b64
                    }},
                    {'type': 'text', 'text': CLASSIFICATION_PROMPT}
                ]
            }]
        }

        bedrock_response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType='application/json',
            body=json.dumps(request_body)
        )
        result = json.loads(bedrock_response['body'].read())
        parsed = json.loads(result['content'][0]['text'])
        parsed['_analysis_mode'] = 'bedrock'
        return parsed

    except Exception as bedrock_err:
        print(f"[FALLBACK] Bedrock unavailable: {bedrock_err}")
        print("[REKOGNITION] Falling back to Amazon Rekognition label detection")
        return _rekognition_classification(image_bytes)


def _rekognition_classification(image_bytes: bytes) -> dict:
    """
    Real AI fallback using Amazon Rekognition DetectLabels.
    Sends actual image pixels to Rekognition, maps detected object labels
    to sanitation categories, severity and health risk.
    Works with UPI billing — no Bedrock/Marketplace subscription needed.
    """
    rekognition = boto3.client('rekognition', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

    try:
        rek_response = rekognition.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=20,
            MinConfidence=55,
        )
        labels = [l['Name'].lower() for l in rek_response['Labels']]
        top_labels = [l['Name'] for l in rek_response['Labels']]  # preserve original case for description
        avg_confidence = sum(l['Confidence'] for l in rek_response['Labels']) / max(len(rek_response['Labels']), 1)
        print(f"[REKOGNITION] Detected labels: {top_labels}")
    except Exception as rek_err:
        print(f"[REKOGNITION] Failed: {rek_err}. Using last-resort static fallback.")
        return _static_fallback()

    # ── Spam detection ────────────────────────────────────────────────────
    spam_indicators = {'person', 'human', 'face', 'selfie', 'food', 'drink',
                       'beverage', 'meal', 'restaurant', 'indoors', 'furniture',
                       'electronics', 'computer', 'phone', 'vehicle', 'car', 'text', 'document'}
    sanitation_indicators = {'garbage', 'waste', 'trash', 'litter', 'debris', 'dirt',
                             'water', 'flood', 'drain', 'sewer', 'animal', 'carcass',
                             'pollution', 'contamination', 'mud', 'sewage', 'puddle',
                             'plastic', 'bag', 'pile', 'dump', 'rubbish', 'filth'}
    label_set = set(labels)
    has_spam = bool(label_set & spam_indicators)
    has_sanitation = bool(label_set & sanitation_indicators)

    # Only mark spam if no sanitation content at all
    if has_spam and not has_sanitation:
        return {
            'is_spam': True,
            'category': 'other',
            'severity_score': 0,
            'description': 'Image does not appear to show a sanitation issue.',
            'health_risk': 'none',
            'confidence': round(avg_confidence / 100, 2),
            '_analysis_mode': 'rekognition',
        }

    # ── Category mapping — scored by label matches ────────────────────────
    category_rules = {
        'garbage_pile':     ['garbage', 'waste', 'trash', 'litter', 'debris', 'rubbish',
                             'plastic', 'bag', 'pile', 'dump', 'filth', 'bin', 'container'],
        'stagnant_water':   ['water', 'flood', 'puddle', 'pool', 'flooding', 'waterlogged',
                             'liquid', 'mud', 'swamp', 'wetland'],
        'overflowing_drain':['drain', 'gutter', 'overflow', 'flooding', 'water', 'pipe',
                             'sewer', 'manhole', 'channel'],
        'blocked_sewer':    ['sewer', 'sewage', 'manhole', 'pipe', 'blockage', 'drain',
                             'overflow', 'contamination'],
        'medical_waste':    ['medical', 'hospital', 'syringe', 'needle', 'bandage', 'glove',
                             'biohazard', 'clinical', 'pharmaceutical'],
        'animal_carcass':   ['animal', 'carcass', 'dead', 'dog', 'cat', 'bird', 'rat',
                             'wildlife', 'mammal', 'reptile'],
    }

    scores = {cat: 0 for cat in category_rules}
    for cat, keywords in category_rules.items():
        for keyword in keywords:
            if any(keyword in lbl for lbl in labels):
                scores[cat] += 1

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    # If no category matched at all, default to garbage_pile (most common)
    if best_score == 0:
        best_category = 'garbage_pile'

    # ── Severity from label count + category weight ───────────────────────
    category_base_severity = {
        'garbage_pile': 5,
        'overflowing_drain': 6,
        'blocked_sewer': 7,
        'stagnant_water': 6,
        'medical_waste': 9,
        'animal_carcass': 8,
    }
    severity = min(10, category_base_severity.get(best_category, 5) + min(best_score - 1, 2))

    # ── Health risk ───────────────────────────────────────────────────────
    health_risk_map = {
        'garbage_pile': 'medium' if severity < 7 else 'high',
        'overflowing_drain': 'medium' if severity < 7 else 'high',
        'blocked_sewer': 'high',
        'stagnant_water': 'high',
        'medical_waste': 'high',
        'animal_carcass': 'high',
    }

    # ── Description from actual detected labels ───────────────────────────
    visible = ', '.join(top_labels[:5]) if top_labels else 'sanitation issue'
    description_templates = {
        'garbage_pile': f'Waste accumulation detected in the area. Visual analysis identified: {visible}. Immediate cleanup required to prevent health hazards.',
        'stagnant_water': f'Standing water detected. Visual analysis identified: {visible}. Stagnant water poses mosquito breeding and contamination risk.',
        'overflowing_drain': f'Drain overflow detected. Visual analysis identified: {visible}. Blocked drainage causing water accumulation on the surface.',
        'blocked_sewer': f'Sewer blockage detected. Visual analysis identified: {visible}. Sewage backup risk may contaminate surrounding area.',
        'medical_waste': f'Medical waste detected in open area. Visual analysis identified: {visible}. Biohazard risk requires specialized disposal team.',
        'animal_carcass': f'Animal remains detected. Visual analysis identified: {visible}. Health risk to nearby residents from decomposition.',
    }

    return {
        'is_spam': False,
        'category': best_category,
        'severity_score': severity,
        'description': description_templates.get(best_category, f'Sanitation issue detected. Visual analysis identified: {visible}.'),
        'health_risk': health_risk_map.get(best_category, 'medium'),
        'confidence': round(min(avg_confidence / 100, 0.95), 2),
        'rekognition_labels': top_labels,
        '_analysis_mode': 'rekognition',
    }


def _static_fallback() -> dict:
    """Last resort if both Bedrock and Rekognition fail."""
    return {
        'is_spam': False,
        'category': 'garbage_pile',
        'severity_score': 5,
        'description': 'Sanitation issue reported by citizen. Manual inspection required.',
        'health_risk': 'medium',
        'confidence': 0.5,
        '_analysis_mode': 'static_fallback',
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /reports — create a new report and auto-create its task
# ─────────────────────────────────────────────────────────────────────────────

def create_report(body: dict) -> dict:
    """
    Main report creation logic:
    1. Call Bedrock AI with the S3 image
    2. Reject spam
    3. Save report to DynamoDB
    4. Auto-create a Task record for this report
    5. Return ticket_id + ai_analysis to the frontend
    """
    image_key = body.get('image_key', '')
    latitude = float(body.get('latitude', 0))
    longitude = float(body.get('longitude', 0))
    voice_key = body.get('voice_key', '')
    ward_number = int(body.get('ward_number', 0))

    if not image_key:
        raise ValueError("image_key is required")

    # ── Step 1: Real AI classification ────────────────────────────────────
    ai_analysis = analyze_image_from_s3(image_key)

    # ── Step 2: Reject spam ────────────────────────────────────────────────
    if ai_analysis.get('is_spam', False):
        return {
            'ticket_id': None,
            'status': 'rejected',
            'reason': 'Image does not appear to show a sanitation issue.',
            'ai_analysis': ai_analysis,
        }

    # ── Step 3: Save report ────────────────────────────────────────────────
    ticket_id = generate_ticket_id()
    now = _now()

    report = {
        'PK': f'REPORT#{ticket_id}',
        'SK': 'META',
        'ticket_id': ticket_id,
        'image_key': image_key,
        'voice_key': voice_key,
        'latitude': Decimal(str(round(latitude, 6))),
        'longitude': Decimal(str(round(longitude, 6))),
        'ward_number': ward_number,
        'category': ai_analysis['category'],
        'severity_score': ai_analysis['severity_score'],
        'description': ai_analysis['description'],
        'health_risk': ai_analysis['health_risk'],
        'is_spam': False,
        'ai_confidence': Decimal(str(round(ai_analysis.get('confidence', 0), 4))),
        'status': 'pending',
        'created_at': now,
        'updated_at': now,
        # GSI1 so dashboard can query by status
        'GSI1PK': 'STATUS#pending',
        'GSI1SK': now,
    }
    table.put_item(Item=report)

    # ── Step 4: Auto-create Task ───────────────────────────────────────────
    priority, sla_hours = _priority_from_severity(ai_analysis['severity_score'])
    task_id = f"TSK-{datetime.utcnow().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    task = {
        'PK': f'TASK#{task_id}',
        'SK': 'META',
        'task_id': task_id,
        'report_ticket': ticket_id,
        'image_key': image_key,          # before-photo key (needed for validation)
        'after_image_key': '',
        'status': 'pending',
        'priority': priority,
        'sla_hours': sla_hours,
        'category': ai_analysis['category'],
        'severity_score': ai_analysis['severity_score'],
        'health_risk': ai_analysis['health_risk'],
        'description': ai_analysis['description'],
        'ward_number': ward_number,
        'latitude': Decimal(str(round(latitude, 6))),  # Decimal required by DynamoDB
        'longitude': Decimal(str(round(longitude, 6))),
        'assigned_worker_id': None,
        'worker_notes': '',
        'created_at': now,
        'updated_at': now,
        'GSI1PK': 'STATUS#pending',
        'GSI1SK': now,
    }
    table.put_item(Item=task)

    # ── Step 5: Return to frontend ─────────────────────────────────────────
    return {
        'ticket_id': ticket_id,
        'status': 'pending',
        'ai_analysis': ai_analysis,
        'message': 'Report submitted successfully',
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /reports — list all reports (with optional ward filter)
# ─────────────────────────────────────────────────────────────────────────────

def list_reports(query_params: dict) -> list:
    limit = min(int(query_params.get('limit', 50)), 100)
    status_filter = query_params.get('status', '')
    ward_filter = query_params.get('ward', '')

    filter_expr = Attr('SK').eq('META') & Attr('PK').begins_with('REPORT#')
    if status_filter:
        filter_expr = filter_expr & Attr('status').eq(status_filter)
    if ward_filter:
        filter_expr = filter_expr & Attr('ward_number').eq(int(ward_filter))

    response = table.scan(FilterExpression=filter_expr, Limit=limit * 3)
    items = response.get('Items', [])
    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return items[:limit]


# ─────────────────────────────────────────────────────────────────────────────
# GET /reports/{ticket_id} — get a single report
# ─────────────────────────────────────────────────────────────────────────────

def get_report(ticket_id: str) -> dict | None:
    response = table.get_item(Key={'PK': f'REPORT#{ticket_id}', 'SK': 'META'})
    return response.get('Item')


# ─────────────────────────────────────────────────────────────────────────────
# PUT /reports/{ticket_id}/rate — citizen rates the resolved complaint
# ─────────────────────────────────────────────────────────────────────────────

def rate_report(ticket_id: str, rating: int, feedback: str = '') -> dict:
    """
    Citizen submits a 1-5 star rating for a resolved complaint.
    - Saves citizen_rating to the REPORT item
    - Finds the associated TASK and its assigned worker
    - Updates the WORKER profile's avg_rating with a rolling average
    """
    if not (1 <= rating <= 5):
        raise ValueError('Rating must be between 1 and 5')

    report = table.get_item(Key={'PK': f'REPORT#{ticket_id}', 'SK': 'META'}).get('Item')
    if not report:
        raise ValueError(f'Ticket {ticket_id} not found')

    # Idempotent: return existing rating if already submitted
    if report.get('citizen_rating'):
        return {
            'ticket_id': ticket_id,
            'rating': int(report['citizen_rating']),
            'message': 'Already rated',
            'already_rated': True,
        }

    now = _now()
    table.update_item(
        Key={'PK': f'REPORT#{ticket_id}', 'SK': 'META'},
        UpdateExpression='SET citizen_rating = :r, citizen_feedback = :f, rated_at = :t',
        ExpressionAttributeValues={':r': rating, ':f': feedback, ':t': now},
    )

    # Find the task linked to this report to get the assigned worker
    task_resp = table.scan(
        FilterExpression=Attr('report_ticket').eq(ticket_id) & Attr('SK').eq('META')
    )
    tasks = task_resp.get('Items', [])
    if tasks:
        assigned_worker = tasks[0].get('assigned_worker_id')
        if assigned_worker:
            # Rolling average: new_avg = (old_avg * old_count + rating) / new_count
            prof_resp = table.get_item(
                Key={'PK': f'WORKER#{assigned_worker}', 'SK': 'PROFILE'}
            )
            profile = prof_resp.get('Item', {})
            old_avg = float(profile.get('avg_rating') or 0)
            old_count = int(profile.get('rating_count') or 0)
            new_count = old_count + 1
            new_avg = round((old_avg * old_count + rating) / new_count, 2)
            table.update_item(
                Key={'PK': f'WORKER#{assigned_worker}', 'SK': 'PROFILE'},
                UpdateExpression='SET avg_rating = :r, rating_count = :c',
                ExpressionAttributeValues={
                    ':r': Decimal(str(new_avg)),
                    ':c': new_count,
                },
            )

    return {'ticket_id': ticket_id, 'rating': rating, 'message': 'Thank you for your feedback!'}


# ─────────────────────────────────────────────────────────────────────────────
# Handler — route by HTTP method + path
# ─────────────────────────────────────────────────────────────────────────────

def handler(event, context):
    try:
        method = event.get('httpMethod', 'POST')
        path = event.get('path', '/reports')
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}

        # POST /reports
        if method == 'POST' and path.rstrip('/') == '/reports':
            result = create_report(body)
            status = 400 if result.get('status') == 'rejected' else 200
            return _response(status, result)

        # GET /reports/{ticket_id}
        elif method == 'GET' and path_params.get('ticket_id'):
            ticket_id = path_params['ticket_id'].upper()
            report = get_report(ticket_id)
            if report is None:
                return _response(404, {'error': f'Ticket {ticket_id} not found'})
            return _response(200, report)

        # PUT /reports/{ticket_id}/rate
        elif method == 'PUT' and path_params.get('ticket_id') and path.endswith('/rate'):
            ticket_id = path_params['ticket_id'].upper()
            raw_rating = body.get('rating')
            if raw_rating is None:
                return _response(400, {'error': 'rating is required'})
            result = rate_report(ticket_id, int(raw_rating), body.get('feedback', ''))
            return _response(200, result)

        # GET /reports
        elif method == 'GET' and '/reports' in path:
            reports = list_reports(query_params)
            return _response(200, {'reports': reports, 'count': len(reports)})

        return _response(404, {'error': 'Route not found'})

    except ValueError as e:
        return _response(400, {'error': str(e)})
    except Exception as e:
        return _response(500, {'error': str(e)})


# ─── Local smoke test (tests what doesn't need AWS) ─────────────────────────
if __name__ == '__main__':
    print("Testing generate_ticket_id()...")
    for _ in range(5):
        tid = generate_ticket_id()
        assert tid.startswith('SAN') and len(tid) == 9
    print(f"  Sample: {generate_ticket_id()} ✓")

    print("Testing _priority_from_severity()...")
    assert _priority_from_severity(9) == ('critical', 4)
    assert _priority_from_severity(5) == ('medium', 24)
    print("  ✓")

    print("\nSmoke tests passed. Full handler requires real AWS + S3 image.")
