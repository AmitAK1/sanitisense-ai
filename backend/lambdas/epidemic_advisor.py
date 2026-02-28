"""
SanitiSense AI — Epidemic Risk Advisor Lambda
AI health risk advisories for wards.

Trigger:
  GET /epidemic?ward=N         → advisory for a specific ward
  GET /epidemic/city-overview  → city-wide risk summary

TWO MODES:
  Mode 1 — RAG (Bedrock Knowledge Base):
    When KNOWLEDGE_BASE_ID is set, Claude retrieves from WHO WASH docs first.
    Response includes data_source: "rag"

  Mode 2 — Direct Bedrock fallback:
    When KNOWLEDGE_BASE_ID is not set (or equals 'YOUR_KB_ID'), Claude uses its
    own training knowledge. Still accurate, just not grounded in specific docs.
    Response includes data_source: "bedrock_direct"

FRONTEND expects structured fields (not just a wall of text):
  - advisory (string)
  - diseases_at_risk (array of strings)
  - recommended_actions (array of strings)
  - risk_level (low/medium/high/critical)
  - data_source (rag/bedrock_direct)
"""

import json
import os
import re
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SanitiSense'))

KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', '')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')

# Lazy-init clients (avoids credential errors during unit testing)
_bedrock = None
_bedrock_agent = None


def _get_bedrock():
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    return _bedrock


def _get_bedrock_agent():
    global _bedrock_agent
    if _bedrock_agent is None:
        _bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    return _bedrock_agent


def _get_current_season() -> str:
    month = datetime.utcnow().month
    if month in (6, 7, 8, 9):
        return 'monsoon'
    elif month in (10, 11):
        return 'post-monsoon'
    elif month in (12, 1, 2):
        return 'winter'
    return 'summer'


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Collect ward stats from DynamoDB
# ─────────────────────────────────────────────────────────────────────────────

def get_ward_stats(ward_number: int) -> dict:
    """
    Aggregate sanitation stats for a ward from the real DynamoDB data.
    Fixed: uses boto3 Attr conditions correctly (the original had broken syntax).
    """
    response = table.scan(
        FilterExpression=(
            Attr('PK').begins_with('REPORT#') &
            Attr('SK').eq('META') &
            Attr('ward_number').eq(ward_number)
        )
    )
    items = response.get('Items', [])

    categories: dict[str, int] = {}
    total_severity = 0
    stagnant_water_count = 0

    for item in items:
        cat = item.get('category', 'other')
        categories[cat] = categories.get(cat, 0) + 1
        total_severity += int(item.get('severity_score', 0))
        if cat == 'stagnant_water':
            stagnant_water_count += 1

    top_categories = ', '.join(
        f"{k} ({v})"
        for k, v in sorted(categories.items(), key=lambda x: -x[1])[:5]
    ) or 'no reports'

    avg_severity = round(total_severity / max(len(items), 1), 1)

    return {
        'ward_number': ward_number,
        'open_reports': len(items),
        'top_categories': top_categories,
        'avg_severity': avg_severity,
        'stagnant_water_count': stagnant_water_count,
        'season': _get_current_season(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Step 2A: RAG mode — Bedrock Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────

def _query_rag(query_text: str) -> dict:
    """Query Bedrock Knowledge Base (grounded advisory)."""
    agent = _get_bedrock_agent()
    response = agent.retrieve_and_generate(
        input={'text': query_text},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                'modelArn': (
                    f'arn:aws:bedrock:{os.environ.get("AWS_REGION", "us-east-1")}'
                    f'::foundation-model/{BEDROCK_MODEL_ID}'
                ),
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {'numberOfResults': 5}
                }
            }
        }
    )
    citations = []
    for c in response.get('citations', []):
        refs = c.get('retrievedReferences', [])
        if refs:
            try:
                citations.append({
                    'text': c['generatedResponsePart']['textResponsePart']['text'],
                    'source': refs[0]['location']['s3Location']['uri'],
                })
            except (KeyError, IndexError):
                pass
    return {'text': response['output']['text'], 'citations': citations, 'source': 'rag'}


# ─────────────────────────────────────────────────────────────────────────────
# Step 2B: Direct mode — Bedrock without RAG (fallback)
# ─────────────────────────────────────────────────────────────────────────────

DIRECT_PROMPT_TEMPLATE = """You are an expert epidemiologist advising a municipal health authority in India.

Sanitation data for Ward {ward_number}:
- {open_reports} open sanitation reports in the last 7 days
- Most common issues: {top_categories}
- Average severity score: {avg_severity}/10
- Stagnant water reports: {stagnant_water_count}
- Season: {season}

Based on WHO WASH guidelines and Indian epidemiology, provide a structured health risk assessment.

Return ONLY valid JSON (no extra text):
{{
  "risk_level": "low" | "medium" | "high" | "critical",
  "advisory": "3-4 sentence summary of the health situation",
  "diseases_at_risk": ["Dengue", "Malaria"],
  "recommended_actions": [
    "action 1",
    "action 2",
    "action 3"
  ]
}}"""


def _query_direct(stats: dict) -> dict:
    """Call Bedrock directly (no RAG) and parse structured JSON response."""
    bedrock = _get_bedrock()
    prompt = DIRECT_PROMPT_TEMPLATE.format(**stats)

    request_body = {
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 1024,
        'messages': [{'role': 'user', 'content': prompt}],
    }
    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType='application/json',
        body=json.dumps(request_body),
    )
    result = json.loads(response['body'].read())
    raw_text = result['content'][0]['text']

    # Parse JSON from the response text
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # Claude sometimes wraps JSON in markdown — strip it
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        parsed = json.loads(match.group()) if match else {}

    return {
        'text': parsed.get('advisory', raw_text),
        'risk_level': parsed.get('risk_level', 'medium'),
        'diseases_at_risk': parsed.get('diseases_at_risk', []),
        'recommended_actions': parsed.get('recommended_actions', []),
        'citations': [],
        'source': 'bedrock_direct',
    }


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Parse structured fields from RAG text (if in RAG mode)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_rag_advisory(text: str, stats: dict) -> dict:
    """
    RAG returns free-form text. Parse key structured fields from it.
    This gives the frontend the arrays it needs without breaking the text display.
    """
    # Determine risk level from avg_severity
    avg = stats.get('avg_severity', 0)
    if avg >= 8 or stats.get('stagnant_water_count', 0) >= 5:
        risk_level = 'critical'
    elif avg >= 6:
        risk_level = 'high'
    elif avg >= 4:
        risk_level = 'medium'
    else:
        risk_level = 'low'

    # Extract disease names mentioned in the advisory
    known_diseases = ['Dengue', 'Malaria', 'Cholera', 'Leptospirosis', 'Typhoid',
                      'Hepatitis', 'Diarrhea', 'Dysentery', 'Encephalitis']
    diseases_at_risk = [d for d in known_diseases if d.lower() in text.lower()]

    # Heuristic: extract bullet points / numbered list items as recommended actions
    action_lines = re.findall(r'(?:^|\n)\s*(?:\d+\.|[-•*])\s*(.+)', text)
    recommended_actions = [a.strip() for a in action_lines[:6] if len(a.strip()) > 10]

    # Fallback actions if none found
    if not recommended_actions:
        if stats.get('stagnant_water_count', 0) > 0:
            recommended_actions.append('Initiate anti-larval treatment in stagnant water areas')
        if stats.get('avg_severity', 0) >= 6:
            recommended_actions.append('Deploy emergency cleanup crews within 24 hours')
        recommended_actions.append('Issue citizen advisory through ward office and local media')

    return {
        'risk_level': risk_level,
        'diseases_at_risk': diseases_at_risk,
        'recommended_actions': recommended_actions,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main advisor function
# ─────────────────────────────────────────────────────────────────────────────

def get_ward_advisory(ward_number: int) -> dict:
    """Orchestrates the full advisory generation for a single ward."""
    stats = get_ward_stats(ward_number)

    kb_configured = KNOWLEDGE_BASE_ID and KNOWLEDGE_BASE_ID not in ('YOUR_KB_ID', '')

    if kb_configured:
        # RAG mode — grounded in real documents
        query = (
            f"Based on WHO guidelines, what diseases are at risk in an Indian ward "
            f"with {stats['open_reports']} sanitation reports including "
            f"{stats['top_categories']}, average severity {stats['avg_severity']}/10, "
            f"during {stats['season']} season? "
            f"Provide risk level, specific diseases, and recommended actions."
        )
        ai_response = _query_rag(query)
        structured = _parse_rag_advisory(ai_response['text'], stats)
    else:
        # Direct Bedrock mode — no KB needed
        ai_response = _query_direct(stats)
        structured = {
            'risk_level': ai_response.get('risk_level', 'medium'),
            'diseases_at_risk': ai_response.get('diseases_at_risk', []),
            'recommended_actions': ai_response.get('recommended_actions', []),
        }

    return {
        'ward_number': ward_number,
        'risk_level': structured['risk_level'],
        'stats': stats,
        'advisory': ai_response['text'],
        'diseases_at_risk': structured['diseases_at_risk'],
        'recommended_actions': structured['recommended_actions'],
        'citations': ai_response.get('citations', []),
        'data_source': ai_response.get('source', 'bedrock_direct'),
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    }


# ─────────────────────────────────────────────────────────────────────────────
# City-wide overview
# ─────────────────────────────────────────────────────────────────────────────

MUMBAI_WARD_NUMBERS = [1, 3, 5, 7, 10, 12, 15, 18, 22, 24]
MUMBAI_WARD_NAMES = {
    1: 'Colaba', 3: 'Byculla', 5: 'Dadar', 7: 'Andheri East',
    10: 'Kurla', 12: 'Borivali', 15: 'Thane Road', 18: 'Malad',
    22: 'Jogeshwari', 24: 'Goregaon',
}


def get_city_overview() -> dict:
    """
    Aggregate stats across all wards from real DynamoDB data.
    Returns which wards are high-risk + a short city summary.
    Avoids calling Bedrock in a loop (too expensive) — uses heuristic risk assessment.
    """
    response = table.scan(
        FilterExpression=(
            Attr('PK').begins_with('REPORT#') &
            Attr('SK').eq('META')
        )
    )
    items = response.get('Items', [])

    # Aggregate by ward
    ward_data: dict[int, list] = {}
    for item in items:
        wn = int(item.get('ward_number', 0))
        if wn:
            ward_data.setdefault(wn, []).append(item)

    high_risk_wards = []
    total_open = 0

    for wn in MUMBAI_WARD_NUMBERS:
        ward_items = ward_data.get(wn, [])
        open_count = sum(1 for i in ward_items if i.get('status') in ('pending', 'in_progress'))
        total_open += open_count

        severities = [float(i.get('severity_score', 0)) for i in ward_items if i.get('severity_score')]
        avg_sev = sum(severities) / max(len(severities), 1) if severities else 0
        stagnant = sum(1 for i in ward_items if i.get('category') == 'stagnant_water')

        if avg_sev >= 7 or stagnant >= 3:
            risk_level = 'high'
        elif avg_sev >= 5:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        if risk_level == 'high':
            high_risk_wards.append({
                'ward_number': wn,
                'name': MUMBAI_WARD_NAMES.get(wn, f'Ward {wn}'),
                'risk_level': risk_level,
                'open_reports': open_count,
            })

    # Overall city risk
    overall_risk = 'high' if len(high_risk_wards) >= 3 else 'medium' if high_risk_wards else 'low'

    return {
        'city': 'Mumbai',
        'overall_risk': overall_risk,
        'high_risk_wards': high_risk_wards,
        'total_open_reports': total_open,
        'advisory_summary': (
            f"{len(high_risk_wards)} ward(s) at high epidemic risk. "
            f"Total {total_open} open reports across Mumbai. "
            f"Priority: stagnant water areas and high-severity clusters."
        ),
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main handler
# ─────────────────────────────────────────────────────────────────────────────

def handler(event, context):
    try:
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}

        if 'city' in path:
            result = get_city_overview()
        else:
            ward_number = int(query_params.get('ward', 1))
            result = get_ward_advisory(ward_number)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(result, default=str),
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


# ─── Local smoke test ────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Testing _get_current_season()...")
    assert _get_current_season() in ('monsoon', 'post-monsoon', 'winter', 'summer')
    print(f"  Season: {_get_current_season()} ✓")

    print("Testing _parse_rag_advisory()...")
    sample_text = (
        "The ward faces high dengue risk due to stagnant water. "
        "1. Deploy fogging teams immediately\n"
        "2. Issue citizen advisory\n- Check for water containers"
    )
    parsed = _parse_rag_advisory(sample_text, {'avg_severity': 7, 'stagnant_water_count': 4})
    assert 'Dengue' in parsed['diseases_at_risk']
    assert len(parsed['recommended_actions']) > 0
    assert parsed['risk_level'] in ('low', 'medium', 'high', 'critical')
    print(f"  risk_level={parsed['risk_level']} ✓")
    print(f"  diseases_at_risk={parsed['diseases_at_risk']} ✓")
    print(f"  recommended_actions count={len(parsed['recommended_actions'])} ✓")

    print("\nSmoke tests passed. Bedrock/DynamoDB calls require real AWS.")
