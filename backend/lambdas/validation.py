"""
SanitiSense AI — Validation Lambda
Uses Amazon Bedrock (Claude 3 Sonnet Vision) to compare before/after photos
and verify that a sanitation issue has been properly resolved.
"""

import json
import base64
import os

import boto3
bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SanitiSense'))

BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
S3_BUCKET = os.environ.get('S3_BUCKET', 'sanitisense-media')

# ========== BEDROCK VALIDATION PROMPT ==========
VALIDATION_PROMPT = """You are a sanitation work quality inspector for an Indian municipal corporation.

I'm showing you two photos of the SAME location:
- IMAGE 1 (LEFT): The "BEFORE" photo — the original sanitation issue reported by a citizen
- IMAGE 2 (RIGHT): The "AFTER" photo — taken by the sanitation worker after cleanup

Compare these photos and evaluate whether the sanitation issue has been adequately resolved.

Return ONLY a valid JSON object:
{
  "is_resolved": boolean,
  "resolution_quality": "excellent" | "good" | "partial" | "poor" | "not_resolved",
  "resolution_score": integer 1-10,
  "same_location": boolean,
  "observations": "2-3 sentences describing what changed between before and after",
  "issues_remaining": "Description of any remaining issues, or 'none'",
  "confidence": float 0.0-1.0
}

Scoring guide:
- 9-10: Spotlessly clean, better than original state
- 7-8: Issue fully resolved, area clean
- 5-6: Most of the issue resolved, minor remnants
- 3-4: Partial cleanup, significant issues remain
- 1-2: Barely any improvement, or different location entirely

If the photos appear to be of DIFFERENT locations, set same_location=false and resolution_score=1.
Return ONLY the JSON object, no other text."""


def get_image_bytes(image_key):
    """Download image from S3"""
    response = s3.get_object(Bucket=S3_BUCKET, Key=image_key)
    return response['Body'].read()


def validate_with_bedrock(before_bytes, after_bytes):
    """
    Send before/after images to Bedrock for comparison.
    Uses Claude 3 Sonnet's multi-image vision capability.
    """
    before_b64 = base64.b64encode(before_bytes).decode('utf-8')
    after_b64 = base64.b64encode(after_bytes).decode('utf-8')

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": before_b64
                        }
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": after_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": VALIDATION_PROMPT
                    }
                ]
            }
        ]
    }

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType='application/json',
        body=json.dumps(request_body)
    )
    result = json.loads(response['body'].read())
    return json.loads(result['content'][0]['text'])


def handler(event, context):
    """
    Lambda handler for before/after validation.
    
    Expected event body:
    {
        "task_id": "TSK-260228-ABC123",
        "before_image_key": "citizen-reports/2026/02/28/before.jpg",
        "after_image_key": "worker-completions/2026/02/28/after.jpg"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        task_id = body.get('task_id', '')
        before_key = body.get('before_image_key', '')
        after_key = body.get('after_image_key', '')

        if not all([task_id, before_key, after_key]):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: task_id, before_image_key, after_image_key"})
            }

        # Step 1: Get both images
        before_bytes = get_image_bytes(before_key)
        after_bytes = get_image_bytes(after_key)

        # Step 2: Compare with Bedrock Vision
        validation = validate_with_bedrock(before_bytes, after_bytes)

        # Step 3: Determine new task status
        if validation['resolution_score'] >= 7:
            new_status = 'verified'
        elif validation['resolution_score'] >= 4:
            new_status = 'partial'
        else:
            new_status = 'rejected'

        # Step 4: Update task in DynamoDB
        from datetime import datetime
        now = datetime.utcnow().isoformat() + 'Z'
        table.update_item(
            Key={'PK': f'TASK#{task_id}', 'SK': 'META'},
            UpdateExpression='SET #s = :s, validation = :v, updated_at = :t, GSI1PK = :gsi',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': new_status,
                ':v': validation,
                ':t': now,
                ':gsi': f'STATUS#{new_status}'
            }
        )

        result = {
            "task_id": task_id,
            "new_status": new_status,
            "validation": validation
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result)
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
            "task_id": "TSK-260228-ABC123",
            "before_image_key": "citizen-reports/2026/02/28/before.jpg",
            "after_image_key": "worker-completions/2026/02/28/after.jpg"
        })
    }
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
