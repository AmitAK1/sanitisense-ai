"""
SanitiSense AI — Pre-signed URL Generator Lambda
Allows frontend to upload images DIRECTLY to S3 without going through Lambda.

Why presigned URLs?
  Without this, the frontend would send the photo's bytes through API Gateway →
  Lambda → S3. That route has a 10MB body limit and is very slow.
  With presigned URLs you bypass Lambda entirely for the upload:
    1. GET /upload-url → Lambda gives the frontend a special S3 upload link
    2. Frontend PUTs the raw photo directly to S3 using that link (fast!)
    3. S3 confirms it worked
    4. Frontend sends only the image_key (S3 path) to POST /reports

Trigger: GET /upload-url?filename=photo.jpg&content_type=image/jpeg&type=citizen|worker
"""

import json
import os
import uuid
from datetime import datetime

import boto3

S3_BUCKET = os.environ.get('S3_BUCKET', 'sanitisense-media-982253889131')
s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# File extensions we accept. Anything else gets treated as .jpg for safety.
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'}


def generate_image_key(filename: str, upload_type: str = 'citizen') -> str:
    """
    Build the S3 key (path) where the image will live.
    
    Citizen photos → citizen-reports/YYYY/MM/DD/<8-char-uuid>.<ext>
    Worker after-photos → worker-completions/YYYY/MM/DD/<8-char-uuid>.<ext>

    Example: citizen-reports/2026/02/28/a3f8bb2c.jpg
    """
    # Get file extension, default to jpg if not allowed
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    if ext not in ALLOWED_EXTENSIONS:
        ext = 'jpg'

    now = datetime.utcnow()
    unique_id = uuid.uuid4().hex[:8]
    folder = 'worker-completions' if upload_type == 'worker' else 'citizen-reports'
    return f"{folder}/{now.strftime('%Y/%m/%d')}/{unique_id}.{ext}"


def handler(event, context):
    """
    Generate a presigned S3 URL.
    
    Query parameters:
    - filename (optional) — e.g. "photo.jpg"
    - content_type (optional) — e.g. "image/jpeg"
    - type (optional) — "citizen" or "worker", default "citizen"
    
    Returns:
    {
      "upload_url": "https://s3.amazonaws.com/...",
      "image_key": "citizen-reports/2026/02/28/a3f8bb2c.jpg"
    }
    """
    try:
        params = event.get('queryStringParameters') or {}
        filename = params.get('filename', 'photo.jpg')
        content_type = params.get('content_type', 'image/jpeg')
        upload_type = params.get('type', 'citizen')  # "citizen" or "worker"

        # Build the S3 key
        image_key = generate_image_key(filename, upload_type)

        # Generate the presigned URL (valid for 5 minutes — 300 seconds)
        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': image_key,
                'ContentType': content_type,
            },
            ExpiresIn=300,
        )

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'upload_url': upload_url,
                'image_key': image_key,
                'expires_in_seconds': 300,
                'bucket': S3_BUCKET,
            }),
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': str(e)}),
        }


# ─── Local smoke test (no AWS needed) ───────────────────────────────────────
if __name__ == '__main__':
    print("Testing generate_image_key()...")

    key = generate_image_key('photo.jpg', 'citizen')
    assert key.startswith('citizen-reports/')
    assert key.endswith('.jpg')
    print(f"  Citizen: {key} ✓")

    key = generate_image_key('after.png', 'worker')
    assert key.startswith('worker-completions/')
    assert key.endswith('.png')
    print(f"  Worker: {key} ✓")

    key = generate_image_key('hack.exe', 'citizen')
    assert key.endswith('.jpg'), "Dangerous extension should be replaced with .jpg"
    print(f"  Blocked ext (.exe → .jpg): {key} ✓")

    print("\nAll smoke tests passed ✓")
