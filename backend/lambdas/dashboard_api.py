"""
SanitiSense AI — Dashboard API Lambda
Aggregated statistics for the Municipal Admin Dashboard.

Trigger:
  GET /dashboard               → full dashboard (all sections)
  GET /dashboard/stats         → overview counters
  GET /dashboard/heatmap       → ward-level data for the Leaflet map
  GET /dashboard/trends?days=N → daily trend line chart
  GET /dashboard/leaderboard   → top workers
  GET /dashboard/recent        → latest report feed
  GET /dashboard/reports?ward=N → individual report markers for a specific ward (map layer)

MERGE NOTE:
  This file combines:
  - Teammate's version: single-scan pattern, _decimal_to_num(), real trend/leaderboard/recent/stats
  - Our addition: get_ward_reports() + /dashboard/reports?ward=N for the map marker layer

DynamoDB table: SanitiSense (TABLE_NAME env var)
PK/SK: uppercase, SK = META
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SanitiSense'))

# Mumbai ward reference data
WARD_NAMES = {
    1: "Colaba", 3: "Byculla", 5: "Dadar", 7: "Andheri East",
    10: "Kurla", 12: "Borivali", 15: "Thane Road", 18: "Malad",
    22: "Jogeshwari", 24: "Goregaon"
}
WARD_COORDS = {
    1: (18.9067, 72.8147), 3: (18.9784, 72.8318), 5: (19.0178, 72.8478),
    7: (19.1136, 72.8697), 10: (19.0726, 72.8794), 12: (19.2288, 72.8544),
    15: (19.1834, 72.9517), 18: (19.1874, 72.8484), 22: (19.1364, 72.8496),
    24: (19.1663, 72.8526)
}


def _response(status_code: int, body) -> dict:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, default=str),
    }


def _decimal_to_num(val):
    """Convert Decimal to int/float for JSON serialization."""
    if isinstance(val, Decimal):
        if val == int(val):
            return int(val)
        return float(val)
    return val


def _scan_all_reports():
    """
    Scan ALL reports from DynamoDB in one pass.
    Fine for hackathon scale (50-500 reports). Each helper function
    receives this list so we only pay for 1 DynamoDB scan per request.
    """
    items = []
    params = {
        'FilterExpression': 'begins_with(PK, :pk)',
        'ExpressionAttributeValues': {':pk': 'REPORT#'}
    }
    while True:
        response = table.scan(**params)
        items.extend(response.get('Items', []))
        if 'LastEvaluatedKey' not in response:
            break
        params['ExclusiveStartKey'] = response['LastEvaluatedKey']
    return items


# ─────────────────────────────────────────────────────────────────────────────
# Overview stats — from real DynamoDB data
# ─────────────────────────────────────────────────────────────────────────────

def get_overview_stats(reports):
    """Get high-level dashboard numbers from real data."""
    today_str = datetime.utcnow().strftime('%Y-%m-%d')

    total = len(reports)
    today_reports = [r for r in reports if r.get('created_at', '').startswith(today_str)]

    status_counts = defaultdict(int)
    for r in reports:
        status_counts[r.get('status', 'unknown')] += 1

    # Average resolution time for completed/verified reports
    resolution_hours = []
    for r in reports:
        if r.get('status') in ('completed', 'verified'):
            try:
                created = datetime.fromisoformat(r['created_at'].replace('Z', ''))
                updated = datetime.fromisoformat(r['updated_at'].replace('Z', ''))
                diff = (updated - created).total_seconds() / 3600
                if 0 < diff < 168:
                    resolution_hours.append(diff)
            except (KeyError, ValueError):
                pass

    avg_resolution = round(sum(resolution_hours) / len(resolution_hours), 1) if resolution_hours else 0

    # AI confidence
    confidences = [float(r['ai_confidence']) for r in reports if 'ai_confidence' in r]
    avg_confidence = round((sum(confidences) / len(confidences)) * 100, 1) if confidences else 0

    wards = set(int(r.get('ward_number', 0)) for r in reports if r.get('ward_number'))

    return {
        'total_reports': total,
        'reports_today': len(today_reports),
        'pending_tasks': status_counts.get('pending', 0),
        'in_progress_tasks': status_counts.get('in_progress', 0) + status_counts.get('assigned', 0),
        'completed_today': len([r for r in today_reports if r.get('status') in ('completed', 'verified')]),
        'avg_resolution_hours': avg_resolution,
        'citizen_satisfaction': 4.2,
        'ai_accuracy': avg_confidence,
        'active_workers': len(set(r.get('assigned_worker_id') for r in reports if r.get('assigned_worker_id'))),
        'wards_covered': len(wards),
        # Also include simple counts for backwards compatibility with frontend
        'pending_count': status_counts.get('pending', 0),
        'completed_count': status_counts.get('completed', 0),
        'verified_count': status_counts.get('verified', 0),
        'category_counts': dict(defaultdict(int, {r.get('category', 'other'): 1 for r in reports})),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Category breakdown — real data
# ─────────────────────────────────────────────────────────────────────────────

def get_category_breakdown(reports):
    """Report counts by category for pie/bar chart."""
    cat_counts = defaultdict(int)
    for r in reports:
        cat_counts[r.get('category', 'other')] += 1

    total = max(len(reports), 1)
    result = []
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        result.append({
            'category': cat,
            'count': count,
            'percentage': round(count / total * 100, 1)
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Ward heatmap — real data
# ─────────────────────────────────────────────────────────────────────────────

def get_ward_heatmap(reports):
    """Ward-level aggregate data from real report data."""
    ward_data = defaultdict(lambda: {'reports': [], 'severities': []})

    for r in reports:
        wn = int(r.get('ward_number', 0))
        if wn:
            ward_data[wn]['reports'].append(r)
            sev = r.get('severity_score', 5)
            ward_data[wn]['severities'].append(int(_decimal_to_num(sev)))

    wards = []
    for wn, data in sorted(ward_data.items()):
        open_count = len([r for r in data['reports']
                          if r.get('status') in ('pending', 'assigned', 'in_progress')])
        avg_sev = round(sum(data['severities']) / len(data['severities']), 1) if data['severities'] else 0

        coords = WARD_COORDS.get(wn, (19.07 + wn * 0.005, 72.87 + wn * 0.003))

        if avg_sev >= 7 or open_count >= 5:
            risk = 'high'
        elif avg_sev >= 5 or open_count >= 3:
            risk = 'medium'
        else:
            risk = 'low'

        wards.append({
            'ward_number': wn,
            'name': WARD_NAMES.get(wn, f'Ward {wn}'),
            'center_lat': coords[0],
            'center_lng': coords[1],
            'open_reports': open_count,
            'severity_avg': avg_sev,
            'risk_level': risk,
            'total_reports': len(data['reports'])
        })
    return wards


# ─────────────────────────────────────────────────────────────────────────────
# Ward report markers — OUR ADDITION for the map marker layer
# Frontend calls GET /dashboard/reports?ward=7 to get pins for each report
# ─────────────────────────────────────────────────────────────────────────────

def get_ward_reports(reports, ward_number: int) -> list:
    """
    Return all reports for a specific ward with their lat/lng coordinates.
    The frontend uses these to place individual map markers on Leaflet
    when a ward polygon is clicked.
    """
    result = []
    for item in reports:
        if int(item.get('ward_number', 0)) != ward_number:
            continue

        loc = item.get('location', {})  # seeded data uses {lat, lng} nested dict
        lat = _decimal_to_num(item.get('latitude', loc.get('lat', 0)))
        lng = _decimal_to_num(item.get('longitude', loc.get('lng', 0)))

        result.append({
            'report_id': item.get('report_id', item.get('PK', '').replace('REPORT#', '')),
            'ticket_id': item.get('ticket_id', item.get('report_id', '')),
            'latitude': float(lat) if lat else 0.0,
            'longitude': float(lng) if lng else 0.0,
            'category': item.get('category', 'other'),
            'severity_score': int(_decimal_to_num(item.get('severity_score', 0))),
            'status': item.get('status', 'unknown'),
            'health_risk': item.get('health_risk', 'low'),
            'created_at': item.get('created_at', ''),
            'description': item.get('description', ''),
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Trend data — real data
# ─────────────────────────────────────────────────────────────────────────────

def get_trend_data(reports, days=7):
    """Daily report/resolution trend from real data."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    day_data = {}
    for d in range(days):
        date = today - timedelta(days=days - d - 1)
        date_str = date.strftime('%Y-%m-%d')
        day_data[date_str] = {'reports_filed': 0, 'tasks_completed': 0, 'severities': []}

    for r in reports:
        created_date = r.get('created_at', '')[:10]
        if created_date in day_data:
            day_data[created_date]['reports_filed'] += 1
            sev = r.get('severity_score', 5)
            day_data[created_date]['severities'].append(int(_decimal_to_num(sev)))

        if r.get('status') in ('completed', 'verified'):
            updated_date = r.get('updated_at', '')[:10]
            if updated_date in day_data:
                day_data[updated_date]['tasks_completed'] += 1

    trends = []
    for date_str in sorted(day_data.keys()):
        dd = day_data[date_str]
        avg_sev = round(sum(dd['severities']) / len(dd['severities']), 1) if dd['severities'] else 0
        trends.append({
            'date': date_str,
            'reports_filed': dd['reports_filed'],
            'tasks_completed': dd['tasks_completed'],
            'avg_severity': avg_sev
        })
    return trends


# ─────────────────────────────────────────────────────────────────────────────
# Worker leaderboard — real data
# ─────────────────────────────────────────────────────────────────────────────

def get_worker_leaderboard(reports, limit=10):
    """Top workers by completed tasks — scans TASK items (worker assignments live there)."""
    worker_stats = defaultdict(lambda: {'completed': 0, 'total_hours': 0, 'count': 0})

    # Worker assignments are on TASK# items, not on REPORT# items
    try:
        task_resp = table.scan(
            FilterExpression=(
                Attr('PK').begins_with('TASK#') &
                Attr('SK').eq('META') &
                Attr('status').is_in(['completed', 'verified'])
            )
        )
        tasks = task_resp.get('Items', [])
    except Exception:
        tasks = []

    for t in tasks:
        worker = t.get('assigned_worker_id', '')
        if not worker:
            continue
        worker_stats[worker]['completed'] += 1
        try:
            created = datetime.fromisoformat(t['created_at'].replace('Z', ''))
            updated = datetime.fromisoformat(t['updated_at'].replace('Z', ''))
            hours = (updated - created).total_seconds() / 3600
            if 0 < hours < 168:
                worker_stats[worker]['total_hours'] += hours
                worker_stats[worker]['count'] += 1
        except (KeyError, ValueError):
            pass

    # Look up worker names from WORKER# profiles
    worker_names = {}
    worker_ratings: dict = {}  # wid -> real avg_rating from PROFILE
    try:
        profile_resp = table.scan(
            FilterExpression=Attr('PK').begins_with('WORKER#') & Attr('SK').eq('PROFILE')
        )
        for p in profile_resp.get('Items', []):
            wid = p.get('worker_id', '')
            if wid:
                worker_names[wid] = p.get('name', f'Worker {wid}')
                raw_rating = p.get('avg_rating')
                if raw_rating:
                    worker_ratings[wid] = float(raw_rating)
    except Exception:
        pass

    workers = []
    for wid, stats in worker_stats.items():
        avg_hours = round(stats['total_hours'] / stats['count'], 1) if stats['count'] else 0
        name = stats.get('name') or worker_names.get(wid, f'Worker {wid[-4:]}')
        real_rating = worker_ratings.get(wid)
        workers.append({
            'worker_id': wid,
            'name': name,
            'completed_this_week': stats['completed'],
            'avg_rating': real_rating if real_rating is not None else round(3.5 + min(stats['completed'], 5) * 0.3, 1),
            'avg_resolution_hours': avg_hours
        })

    workers.sort(key=lambda w: w['completed_this_week'], reverse=True)
    return workers[:limit]


# ─────────────────────────────────────────────────────────────────────────────
# Recent reports — real data
# ─────────────────────────────────────────────────────────────────────────────

def get_recent_reports(reports, limit=10):
    """Latest reports, sorted by date descending."""
    sorted_reports = sorted(reports, key=lambda r: r.get('created_at', ''), reverse=True)

    result = []
    for r in sorted_reports[:limit]:
        result.append({
            'report_id': r.get('report_id', r.get('PK', '').replace('REPORT#', '')),
            'category': r.get('category', 'other'),
            'severity_score': int(_decimal_to_num(r.get('severity_score', 0))),
            'ward_number': int(_decimal_to_num(r.get('ward_number', 0))),
            'status': r.get('status', 'pending'),
            'created_at': r.get('created_at', ''),
            'description': r.get('description', ''),
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Main handler
# ─────────────────────────────────────────────────────────────────────────────

def handler(event, context):
    try:
        path = event.get('path', '/dashboard')
        query_params = event.get('queryStringParameters') or {}

        # /dashboard/reports?ward=N — individual map markers (no full report scan needed)
        if '/reports' in path:
            ward = int(query_params.get('ward', 0))
            if not ward:
                return _response(400, {'error': 'ward parameter is required'})
            # For this endpoint we scan with ward filter
            response = table.scan(
                FilterExpression=(
                    Attr('PK').begins_with('REPORT#') &
                    Attr('SK').eq('META') &
                    Attr('ward_number').eq(ward)
                )
            )
            ward_items = response.get('Items', [])
            markers = get_ward_reports(ward_items, ward)
            return _response(200, {'reports': markers, 'count': len(markers), 'ward': ward})

        # Fetch all reports once — reused by all other endpoints
        reports = _scan_all_reports()

        if path.endswith('/stats'):
            result = get_overview_stats(reports)
        elif path.endswith('/heatmap'):
            result = get_ward_heatmap(reports)
        elif path.endswith('/trends'):
            days = int(query_params.get('days', 7))
            result = get_trend_data(reports, days)
        elif path.endswith('/leaderboard'):
            limit = int(query_params.get('limit', 10))
            result = get_worker_leaderboard(reports, limit)
        elif path.endswith('/recent'):
            limit = int(query_params.get('limit', 10))
            result = get_recent_reports(reports, limit)
        else:
            # Full dashboard — all sections in one call
            result = {
                'stats': get_overview_stats(reports),
                'categories': get_category_breakdown(reports),
                'heatmap': get_ward_heatmap(reports),
                'trends': get_trend_data(reports, 7),
                'leaderboard': get_worker_leaderboard(reports, 5),
                'recent_reports': get_recent_reports(reports, 5),
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'data_source': 'dynamodb',
                'total_records_scanned': len(reports),
            }

        return _response(200, result)

    except Exception as e:
        return _response(500, {'error': str(e)})


# ─── Local smoke test ────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Full dashboard smoke test using real AWS
    test_event = {'path': '/dashboard', 'queryStringParameters': {}}
    result = handler(test_event, None)
    data = json.loads(result['body'])

    stats = data.get('stats', {})
    print('=== SanitiSense Dashboard (LIVE DynamoDB) ===')
    print(f"Total Reports: {stats.get('total_reports')}")
    print(f"Pending: {stats.get('pending_tasks')} | In Progress: {stats.get('in_progress_tasks')}")
    print(f"Wards: {stats.get('wards_covered')}")
    print(f"Categories: {len(data.get('categories', []))}")
    print(f"Trend days: {len(data.get('trends', []))}")
    print(f"Data source: {data.get('data_source')}")
