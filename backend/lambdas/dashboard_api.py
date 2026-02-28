"""
SanitiSense AI — Dashboard API Lambda
Aggregated statistics for the Municipal Admin Dashboard.

Trigger: GET /dashboard           → full dashboard (all sections)
         GET /dashboard/stats     → overview counters
         GET /dashboard/heatmap   → ward-level data for the map
         GET /dashboard/trends    → daily trend line chart
         GET /dashboard/leaderboard → top workers
         GET /dashboard/recent    → latest report feed
         GET /dashboard/reports?ward=N → individual report markers for a ward

DynamoDB table: SanitiSense (TABLE_NAME env var)
PK/SK: uppercase (PK, SK = META for reports)
"""

import json
import os
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SanitiSense'))


def _response(status_code: int, body: dict) -> dict:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, default=str),
    }


# ─────────────────────────────────────────────────────────────────────────────
# REAL: overview stats — scan and count by status
# ─────────────────────────────────────────────────────────────────────────────

def get_overview_stats() -> dict:
    """
    Count reports by status from DynamoDB.
    Scans REPORT# items and aggregates counters.
    At the hackathon scale (50-500 reports) a scan is fine.
    For production scale, use the stats_aggregator Lambda + AggregatedStats table.
    """
    response = table.scan(
        FilterExpression=(
            Attr('SK').eq('META') &
            Attr('PK').begins_with('REPORT#')
        )
    )
    items = response.get('Items', [])

    # Count by status
    status_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    severities = []

    for item in items:
        s = item.get('status', 'unknown')
        status_counts[s] = status_counts.get(s, 0) + 1
        c = item.get('category', 'other')
        category_counts[c] = category_counts.get(c, 0) + 1
        sv = item.get('severity_score', 0)
        if sv:
            severities.append(float(sv))

    avg_severity = round(sum(severities) / max(len(severities), 1), 1)

    return {
        'total_reports': len(items),
        'pending_count': status_counts.get('pending', 0),
        'in_progress_count': status_counts.get('in_progress', 0),
        'completed_count': status_counts.get('completed', 0),
        'verified_count': status_counts.get('verified', 0),
        'avg_severity': avg_severity,
        'category_counts': category_counts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# REAL: recent reports — latest N report items
# ─────────────────────────────────────────────────────────────────────────────

def get_recent_reports(limit: int = 10) -> list:
    """Fetch the N most recent reports, sorted by created_at descending."""
    response = table.scan(
        FilterExpression=(
            Attr('SK').eq('META') &
            Attr('PK').begins_with('REPORT#')
        )
    )
    items = response.get('Items', [])
    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return items[:limit]


# ─────────────────────────────────────────────────────────────────────────────
# REAL: reports for a specific ward — for the map marker layer
# ─────────────────────────────────────────────────────────────────────────────

def get_ward_reports(ward_number: int) -> list:
    """
    Return all reports for a specific ward with their lat/lng.
    Frontend uses these to place individual markers on the Leaflet map
    when a ward is clicked.

    Expected response shape per item (frontend TypeScript interface):
    {
      report_id: string,
      latitude: number,
      longitude: number,
      category: string,
      severity_score: number,
      status: string,
      created_at: string,
      description: string
    }
    """
    response = table.scan(
        FilterExpression=(
            Attr('SK').eq('META') &
            Attr('PK').begins_with('REPORT#') &
            Attr('ward_number').eq(ward_number)
        )
    )
    items = response.get('Items', [])

    # Return only the fields the frontend needs (trim payload size)
    result = []
    for item in items:
        loc = item.get('location', {})  # seeded data uses {lat, lng} nested dict
        # Support both storage formats
        lat = float(item.get('latitude', loc.get('lat', 0)))
        lng = float(item.get('longitude', loc.get('lng', 0)))
        result.append({
            'report_id': item.get('report_id', item.get('PK', '').replace('REPORT#', '')),
            'ticket_id': item.get('ticket_id', item.get('report_id', '')),
            'latitude': lat,
            'longitude': lng,
            'category': item.get('category', 'other'),
            'severity_score': int(item.get('severity_score', 0)),
            'status': item.get('status', 'unknown'),
            'health_risk': item.get('health_risk', 'low'),
            'created_at': item.get('created_at', ''),
            'description': item.get('description', ''),
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MOCK (realistic): Ward heatmap — 10 real Mumbai wards from seeded data
# ─────────────────────────────────────────────────────────────────────────────

def get_ward_heatmap() -> list:
    """
    Returns ward-level aggregate data for the map.
    Uses the same 10 Mumbai wards from seed_data.py.
    Frontend renders these as color-coded ward polygons.
    """
    MUMBAI_WARDS = [
        {'ward_number': 1,  'name': 'Colaba',       'center_lat': 18.9067, 'center_lng': 72.8147},
        {'ward_number': 3,  'name': 'Byculla',       'center_lat': 18.9784, 'center_lng': 72.8318},
        {'ward_number': 5,  'name': 'Dadar',         'center_lat': 19.0178, 'center_lng': 72.8478},
        {'ward_number': 7,  'name': 'Andheri East',  'center_lat': 19.1136, 'center_lng': 72.8697},
        {'ward_number': 10, 'name': 'Kurla',         'center_lat': 19.0726, 'center_lng': 72.8794},
        {'ward_number': 12, 'name': 'Borivali',      'center_lat': 19.2288, 'center_lng': 72.8544},
        {'ward_number': 15, 'name': 'Thane Road',    'center_lat': 19.1834, 'center_lng': 72.9517},
        {'ward_number': 18, 'name': 'Malad',         'center_lat': 19.1874, 'center_lng': 72.8484},
        {'ward_number': 22, 'name': 'Jogeshwari',    'center_lat': 19.1364, 'center_lng': 72.8496},
        {'ward_number': 24, 'name': 'Goregaon',      'center_lat': 19.1663, 'center_lng': 72.8526},
    ]

    # Scan once for aggregation
    response = table.scan(
        FilterExpression=(
            Attr('SK').eq('META') &
            Attr('PK').begins_with('REPORT#')
        )
    )
    items = response.get('Items', [])

    # Group by ward
    ward_data: dict[int, list] = {}
    for item in items:
        wn = int(item.get('ward_number', 0))
        if wn:
            ward_data.setdefault(wn, []).append(item)

    result = []
    for w in MUMBAI_WARDS:
        wn = w['ward_number']
        ward_items = ward_data.get(wn, [])
        severities = [float(i.get('severity_score', 0)) for i in ward_items if i.get('severity_score')]
        avg_sev = round(sum(severities) / max(len(severities), 1), 1) if severities else 0.0
        open_reports = sum(1 for i in ward_items if i.get('status') in ('pending', 'in_progress', 'assigned'))

        risk_level = 'high' if avg_sev >= 7 else 'medium' if avg_sev >= 4 else 'low'

        result.append({
            **w,
            'open_reports': open_reports,
            'total_reports': len(ward_items),
            'severity_avg': avg_sev,
            'risk_level': risk_level,
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MOCK (realistic): Trend data and leaderboard
# ─────────────────────────────────────────────────────────────────────────────

def get_trend_data(days: int = 7) -> list:
    """Daily report/resolution trend. Realistic mock — GSI on date needed for real data."""
    trends = []
    today = datetime.utcnow()
    for d in range(days):
        date = today - timedelta(days=days - d - 1)
        trends.append({
            'date': date.strftime('%Y-%m-%d'),
            'reports_filed': 30 + (d * 3) + (d % 3) * 5,
            'tasks_completed': 25 + (d * 2) + (d % 4) * 3,
            'avg_severity': round(4.5 + (d % 3) * 0.5, 1),
        })
    return trends


def get_worker_leaderboard(limit: int = 10) -> list:
    """Top workers by completed tasks. Realistic mock."""
    workers = [
        {
            'worker_id': f'W-{i:03d}',
            'name': f'Worker {i}',
            'completed_this_week': max(1, 20 - i * 2 + (i % 3)),
            'avg_rating': round(4.0 + (i % 5) * 0.15, 1),
            'avg_resolution_hours': round(3.0 + i * 0.5, 1),
        }
        for i in range(1, limit + 1)
    ]
    return sorted(workers, key=lambda w: w['completed_this_week'], reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main handler
# ─────────────────────────────────────────────────────────────────────────────

def handler(event, context):
    try:
        path = event.get('path', '/dashboard')
        query_params = event.get('queryStringParameters') or {}

        # GET /dashboard/reports?ward=N — individual report markers
        if '/reports' in path:
            ward = int(query_params.get('ward', 0))
            if not ward:
                return _response(400, {'error': 'ward parameter is required'})
            reports = get_ward_reports(ward)
            return _response(200, {'reports': reports, 'count': len(reports), 'ward': ward})

        elif path.endswith('/stats'):
            result = get_overview_stats()

        elif path.endswith('/heatmap'):
            result = {'wards': get_ward_heatmap()}

        elif path.endswith('/trends'):
            days = min(int(query_params.get('days', 7)), 30)
            result = {'trends': get_trend_data(days)}

        elif path.endswith('/leaderboard'):
            limit = min(int(query_params.get('limit', 10)), 20)
            result = {'workers': get_worker_leaderboard(limit)}

        elif path.endswith('/recent'):
            limit = min(int(query_params.get('limit', 10)), 50)
            result = {'reports': get_recent_reports(limit)}

        else:
            # Full dashboard — all sections
            result = {
                'stats':          get_overview_stats(),
                'heatmap':        get_ward_heatmap(),
                'trends':         get_trend_data(7),
                'leaderboard':    get_worker_leaderboard(5),
                'recent_reports': get_recent_reports(5),
                'generated_at':   datetime.utcnow().isoformat() + 'Z',
            }

        return _response(200, result)

    except Exception as e:
        return _response(500, {'error': str(e)})


# ─── Local smoke test ────────────────────────────────────────────────────────
if __name__ == '__main__':
    trends = get_trend_data(7)
    assert len(trends) == 7
    print(f"get_trend_data(7): {len(trends)} days ✓")

    lb = get_worker_leaderboard(5)
    assert len(lb) == 5
    print(f"get_worker_leaderboard(5): {len(lb)} workers ✓")

    print("\nSmoke tests passed. DynamoDB-backed functions require real AWS.")
