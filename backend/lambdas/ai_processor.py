"""
SanitiSense AI — AI Processor Lambda (Background Worker)
Triggered by SQS — NOT by API Gateway.

Why this exists (plain English):
  Asking Claude to analyze an image takes 5–15 seconds. That's too slow for a
  user waiting on a loading spinner after hitting "Submit". So instead of making
  the citizen wait, we:
    1. Save the report instantly and return a ticket ID (< 200ms)
    2. Drop a note into an SQS queue ("hey, analyze this photo")
    3. THIS Lambda picks up that note in the background and does the slow work.
  The citizen can close the app and come back later — their report is safe.

SQS Message format (JSON):
{
    "ticket_id":  "SAN4A2F1B",
    "image_key":  "citizen-reports/2026/02/28/a1b2c3d4.jpg",
    "voice_key":  "citizen-reports/2026/02/28/a1b2c3d4.webm"  // optional
}
"""

import json
import os
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key

# Import our existing image analyzer (same folder)
from lambdas.image_analyzer import get_image_from_s3, analyze_with_bedrock, analyze_with_rekognition

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'sanitisense-main'))


def process_single_report(ticket_id: str, image_key: str):
    """
    Core logic: fetch image → run AI → save results → update status.
    Separated from handler() so it's easy to unit-test.
    """
    # Step 1: Download the image from S3
    image_bytes = get_image_from_s3(image_key)

    # Step 2: Ask Claude AI to classify it
    bedrock_result = analyze_with_bedrock(image_bytes)

    # Step 3: Get extra labels from Rekognition (object detection)
    rekognition_labels = analyze_with_rekognition(image_bytes)

    ai_analysis = {
        **bedrock_result,
        'rekognition_labels': rekognition_labels,
    }

    # Step 4: Update DynamoDB — add AI results, change status
    now = datetime.utcnow().isoformat() + 'Z'

    # Determine task priority from severity so worker sees it immediately
    severity = ai_analysis.get('severity_score', 5)
    if severity >= 8:
        priority = 'critical'
    elif severity >= 6:
        priority = 'high'
    elif severity >= 4:
        priority = 'medium'
    else:
        priority = 'low'

    table.update_item(
        Key={
            'pk': f'REPORT#{ticket_id}',
            'sk': 'METADATA',
        },
        UpdateExpression=(
            'SET #st = :status, '
            'ai_analysis = :ai, '
            'category = :cat, '
            'severity_score = :sev, '
            'health_risk = :hr, '
            'description = :desc, '
            'is_spam = :spam, '
            'priority = :priority, '
            'ai_processed_at = :now'
        ),
        ExpressionAttributeNames={
            '#st': 'status',   # 'status' is a reserved word in DynamoDB
        },
        ExpressionAttributeValues={
            ':status': 'pending' if not ai_analysis.get('is_spam') else 'spam',
            ':ai': ai_analysis,
            ':cat': ai_analysis.get('category', 'other'),
            ':sev': ai_analysis.get('severity_score', 0),
            ':hr': ai_analysis.get('health_risk', 'unknown'),
            ':desc': ai_analysis.get('description', ''),
            ':spam': ai_analysis.get('is_spam', False),
            ':priority': priority,
            ':now': now,
        }
    )

    return {
        'ticket_id': ticket_id,
        'status': 'pending',
        'ai_analysis': ai_analysis,
    }


def handler(event, context):
    """
    SQS trigger handler.
    SQS delivers messages in batches — we process each one individually.
    If one fails, SQS will retry only that message (not the whole batch).

    Returns a partial failure report so SQS knows which messages to retry.
    """
    batch_item_failures = []

    for record in event.get('Records', []):
        message_id = record['messageId']
        try:
            body = json.loads(record['body'])
            ticket_id = body['ticket_id']
            image_key = body['image_key']

            print(f"[ai_processor] Processing {ticket_id} → {image_key}")
            result = process_single_report(ticket_id, image_key)
            print(f"[ai_processor] Done: {ticket_id} → category={result['ai_analysis'].get('category')}, "
                  f"severity={result['ai_analysis'].get('severity_score')}")

        except Exception as e:
            print(f"[ai_processor] ERROR on message {message_id}: {e}")
            # Tell SQS this specific message failed — it will go back to the queue for retry
            batch_item_failures.append({'itemIdentifier': message_id})

    # Return batch failures (empty list = all succeeded)
    return {'batchItemFailures': batch_item_failures}


# ─── Local testing ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Simulate an SQS event structure (the real shape AWS sends)
    test_event = {
        'Records': [
            {
                'messageId': 'test-msg-001',
                'body': json.dumps({
                    'ticket_id': 'SAN123456',
                    'image_key': 'citizen-reports/2026/02/28/test.jpg',
                })
            }
        ]
    }
    print("SQS event shape:")
    print(json.dumps(test_event, indent=2))
    print("\nNote: Actual handler() requires real AWS. Run tests/test_lambdas.py for mocked testing.")
