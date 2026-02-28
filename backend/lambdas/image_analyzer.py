"""
SanitiSense AI — Image Analyzer Lambda
Uses Amazon Bedrock (Claude 3 Sonnet Vision) + Amazon Rekognition to classify sanitation images.
This is the CORE AI function of the entire system.
"""

import json
import base64
import os

import boto3
bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
rekognition = boto3.client('rekognition', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

S3_BUCKET = os.environ.get('S3_BUCKET', 'sanitisense-media')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')

# ========== BEDROCK PROMPT ==========
CLASSIFICATION_PROMPT = """Analyze this photo taken by a citizen reporting a sanitation issue in an Indian city.

Return ONLY a valid JSON object with exactly these fields:
{
  "is_spam": boolean,
  "category": "garbage_pile" | "overflowing_drain" | "blocked_sewer" | "stagnant_water" | "medical_waste" | "animal_carcass" | "other",
  "severity_score": integer 1-10,
  "description": "2-3 sentence human-readable description of issue",
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


def get_image_from_s3(image_key):
    """Download image from S3 and return bytes"""
    response = s3.get_object(Bucket=S3_BUCKET, Key=image_key)
    return response['Body'].read()


def analyze_with_bedrock(image_bytes):
    """
    Send image to Amazon Bedrock Claude 3 Sonnet for classification.
    Returns structured JSON with category, severity, description.
    """
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

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
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": CLASSIFICATION_PROMPT
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


def analyze_with_rekognition(image_bytes):
    """
    Call Amazon Rekognition DetectLabels for supplementary object labels.
    Returns list of detected labels with confidence scores.
    """
    response = rekognition.detect_labels(
        Image={'Bytes': image_bytes},
        MaxLabels=10,
        MinConfidence=70
    )
    return [{"name": l['Name'], "confidence": l['Confidence']} for l in response['Labels']]


def handler(event, context):
    """
    Lambda handler for image analysis.
    
    Expected event body:
    {
        "image_key": "citizen-reports/2026/02/28/abc123.jpg"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        image_key = body.get('image_key', '')

        # Step 1: Get image from S3
        image_bytes = get_image_from_s3(image_key)

        # Step 2: Analyze with Bedrock (Claude 3 Sonnet Vision)
        bedrock_result = analyze_with_bedrock(image_bytes)

        # Step 3: Get supplementary labels from Rekognition
        rekognition_labels = analyze_with_rekognition(image_bytes)

        # Step 4: Merge results
        analysis = {
            **bedrock_result,
            "rekognition_labels": rekognition_labels,
            "image_key": image_key
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(analysis)
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
            "image_key": "citizen-reports/2026/02/28/test.jpg"
        })
    }
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
