"""
SanitiSense AI — Epidemic Risk Advisor Lambda
Uses Amazon Bedrock Knowledge Base (RAG) to generate health risk advisories
grounded in WHO guidelines, disease data, and local sanitation patterns.
"""

import json
import os
from datetime import datetime

import boto3
bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SanitiSense'))

KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', 'YOUR_KB_ID')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')

# ========== RAG QUERY TEMPLATE ==========
RAG_QUERY_TEMPLATE = """Based on the following sanitation data from Ward {ward_number} in the city:
- {open_reports} open sanitation reports in the last 7 days
- Most common issues: {top_categories}
- Average severity score: {avg_severity}
- Stagnant water reports: {stagnant_water_count}
- {season} season conditions

Provide a health risk assessment including:
1. Current epidemic risk level (low/medium/high/critical)
2. Specific diseases that could emerge from these conditions
3. Recommended preventive actions for the municipal corporation
4. Citizen advisory recommendations
5. Priority areas for immediate cleanup

Ground your response in WHO guidelines and established epidemiological data for tropical/Indian cities."""


def get_ward_stats(ward_number):
    """
    Aggregate sanitation stats for a ward from DynamoDB.
    In production, this queries the GSI for recent reports in the ward.
    """
    response = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f'WARD#{ward_number}',
            ':sk': 'REPORT#'
        }
    )
    items = response['Items']

    # Aggregate stats from query results
    categories = {}
    total_severity = 0
    stagnant_water_count = 0
    for item in items:
        cat = item.get('category', 'other')
        categories[cat] = categories.get(cat, 0) + 1
        total_severity += item.get('severity_score', 0)
        if cat == 'stagnant_water':
            stagnant_water_count += 1

    top_categories = ', '.join(f"{k} ({v})" for k, v in sorted(categories.items(), key=lambda x: -x[1])[:5])
    avg_severity = round(total_severity / len(items), 1) if items else 0

    return {
        "ward_number": ward_number,
        "open_reports": len(items),
        "top_categories": top_categories,
        "avg_severity": avg_severity,
        "stagnant_water_count": stagnant_water_count,
        "season": "monsoon"
    }


def query_knowledge_base(query_text):
    """
    Query Bedrock Knowledge Base (RAG) for grounded health advisory.
    
    The Knowledge Base should be pre-loaded with:
    - WHO Water, Sanitation and Hygiene guidelines
    - Indian national disease surveillance data
    - Dengue/Malaria/Cholera prevention protocols
    - Municipal sanitation best practices
    """
    response = bedrock_agent.retrieve_and_generate(
        input={'text': query_text},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                'modelArn': f'arn:aws:bedrock:us-east-1::foundation-model/{BEDROCK_MODEL_ID}',
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5
                    }
                }
            }
        }
    )
    return {
        'text': response['output']['text'],
        'citations': [
            {
                'text': c['generatedResponsePart']['textResponsePart']['text'],
                'source': c['retrievedReferences'][0]['location']['s3Location']['uri']
            }
            for c in response.get('citations', [])
            if c.get('retrievedReferences')
        ]
    }


def handler(event, context):
    """
    Lambda handler for epidemic risk assessment.
    
    GET /epidemic?ward=42             → get current risk for a ward
    GET /epidemic/city-overview       → city-wide risk summary
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        path = event.get('path', '')

        if 'city-overview' in path:
            # TODO: implement city-wide aggregation
            result = {
                "city": "Mumbai",
                "overall_risk": "medium",
                "high_risk_wards": [42, 15, 78],
                "total_open_reports": 156,
                "generated_at": datetime.utcnow().isoformat() + 'Z'
            }
        else:
            ward_number = int(query_params.get('ward', 1))
            
            # Step 1: Get ward statistics
            stats = get_ward_stats(ward_number)

            # Step 2: Build RAG query
            query = RAG_QUERY_TEMPLATE.format(**stats)

            # Step 3: Query Knowledge Base
            rag_response = query_knowledge_base(query)

            result = {
                "ward_number": ward_number,
                "stats": stats,
                "advisory": rag_response["text"],
                "citations": rag_response["citations"],
                "generated_at": datetime.utcnow().isoformat() + 'Z'
            }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result, default=str)
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
        "path": "/epidemic",
        "queryStringParameters": {"ward": "42"}
    }
    result = handler(test_event, None)
    output = json.loads(result["body"])
    print(f"Ward: {output['ward_number']}")
    print(f"Open Reports: {output['stats']['open_reports']}")
    print(f"\n{output['advisory']}")
    print(f"\nCitations ({len(output['citations'])}):")
    for c in output['citations']:
        print(f"  - {c['source']}")
