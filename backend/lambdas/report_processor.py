"""
SanitiSense AI — Report Processor Lambda
Handles new citizen report submissions.
Trigger: POST /reports via API Gateway
"""

import json
import uuid
import os
from datetime import datetime

# TODO: uncomment when deploying to AWS
# import boto3
# dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
# table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'sanitisense-main'))


def generate_ticket_id():
    """Generate a unique ticket ID like SAN123456"""
    return f"SAN{uuid.uuid4().hex[:6].upper()}"


def handler(event, context):
    """
    Lambda handler for processing new citizen reports.
    
    Expected event body (JSON):
    {
        "image_key": "citizen-reports/2026/02/28/abc123.jpg",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "voice_key": "citizen-reports/2026/02/28/abc123.webm"  (optional)
    }
    """
    try:
        # Parse input
        body = json.loads(event.get('body', '{}'))
        image_key = body.get('image_key', '')
        latitude = body.get('latitude', 0)
        longitude = body.get('longitude', 0)
        voice_key = body.get('voice_key', '')

        # Generate ticket ID
        ticket_id = generate_ticket_id()

        # TODO: Call image_analyzer to get AI classification
        # For now, return mock analysis
        ai_analysis = {
            "is_spam": False,
            "category": "garbage_pile",
            "severity_score": 7,
            "description": "Moderate garbage accumulation near residential area. Mixed waste including plastic and organic materials visible.",
            "health_risk": "medium",
            "confidence": 0.89
        }

        # Build report record
        report = {
            "pk": f"REPORT#{ticket_id}",
            "sk": "METADATA",
            "ticket_id": ticket_id,
            "image_key": image_key,
            "voice_key": voice_key,
            "latitude": str(latitude),
            "longitude": str(longitude),
            "category": ai_analysis["category"],
            "severity_score": ai_analysis["severity_score"],
            "description": ai_analysis["description"],
            "health_risk": ai_analysis["health_risk"],
            "is_spam": ai_analysis["is_spam"],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        # TODO: Save to DynamoDB
        # table.put_item(Item=report)

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "ticket_id": ticket_id,
                "status": "pending",
                "ai_analysis": ai_analysis,
                "message": "Report submitted successfully"
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }


# Local testing
if __name__ == "__main__":
    test_event = {
        "body": json.dumps({
            "image_key": "citizen-reports/2026/02/28/test.jpg",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
    }
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
