"""Quick test: Can we call Amazon Bedrock?"""
import json
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Test 1: Try Claude Sonnet 4 (latest)
models_to_try = [
    ('us.anthropic.claude-sonnet-4-20250514-v1:0', 'Claude Sonnet 4'),
    ('us.anthropic.claude-3-5-haiku-20241022-v1:0', 'Claude 3.5 Haiku'),
    ('amazon.titan-text-express-v1', 'Amazon Titan Text Express'),
]

request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 100,
    "messages": [
        {"role": "user", "content": "Say 'SanitiSense AI is ready!' in exactly those words."}
    ]
}

titan_body = {
    "inputText": "Say 'SanitiSense AI is ready!'",
    "textGenerationConfig": {"maxTokenCount": 100, "temperature": 0}
}

for model_id, name in models_to_try:
    try:
        print(f"Trying {name} ({model_id})...")
        body = titan_body if 'titan' in model_id else request_body
        response = bedrock.invoke_model(
            modelId=model_id,
            contentType='application/json',
            body=json.dumps(body)
        )
        result = json.loads(response['body'].read())
        if 'content' in result:
            print(f"  SUCCESS! Response: {result['content'][0]['text']}")
        elif 'results' in result:
            print(f"  SUCCESS! Response: {result['results'][0]['outputText']}")
        else:
            print(f"  SUCCESS! Response: {json.dumps(result)[:200]}")
        break
    except Exception as e:
        print(f"  FAILED: {str(e)[:120]}")
        continue
else:
    print("\nNo models worked. You may need to submit Anthropic use case details.")
