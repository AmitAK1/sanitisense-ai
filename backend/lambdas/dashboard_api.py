"""
SanitiSense AI — Dashboard API Lambda
Provides aggregated statistics for the Municipal Admin Dashboard.
Queries DynamoDB for report counts, task statuses, ward-level heatmap data, and trends.
"""

import json
import os
from datetime import datetime, timedelta

# TODO: uncomment when deploying to AWS
# import boto3
# dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
# table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SanitiSense'))


def get_overview_stats():
    """Get high-level dashboard numbers"""
    # TODO: replace with real DynamoDB queries when deploying
    # Use GSI1 to count by status
    
    return {
        "total_reports": 1247,
        "reports_today": 34,
        "pending_tasks": 89,
        "in_progress_tasks": 45,
        "completed_today": 23,
        "avg_resolution_hours": 6.4,
        "citizen_satisfaction": 4.2,
        "ai_accuracy": 94.6,
        "active_workers": 67,
        "wards_covered": 24
    }


def get_category_breakdown():
    """Report counts by category for pie/bar chart"""
    return [
        {"category": "garbage_pile", "count": 423, "percentage": 33.9},
        {"category": "overflowing_drain", "count": 312, "percentage": 25.0},
        {"category": "blocked_sewer", "count": 198, "percentage": 15.9},
        {"category": "stagnant_water", "count": 156, "percentage": 12.5},
        {"category": "medical_waste", "count": 67, "percentage": 5.4},
        {"category": "animal_carcass", "count": 34, "percentage": 2.7},
        {"category": "other", "count": 57, "percentage": 4.6}
    ]


def get_ward_heatmap():
    """Ward-level data for map visualization"""
    # Mock data — in production, aggregate from DynamoDB
    wards = []
    for i in range(1, 25):
        wards.append({
            "ward_number": i,
            "name": f"Ward {i}",
            "center_lat": 19.0 + (i * 0.005),  # Mumbai approximate
            "center_lng": 72.8 + (i * 0.003),
            "open_reports": max(0, 30 - i + (i % 7) * 3),
            "severity_avg": round(3 + (i % 5) * 1.2, 1),
            "risk_level": "high" if i in [3, 7, 15, 22] else "medium" if i % 3 == 0 else "low"
        })
    return wards


def get_trend_data(days=7):
    """Daily report/resolution trend for line chart"""
    trends = []
    base_date = datetime(2026, 2, 28)
    for d in range(days):
        date = base_date - timedelta(days=days - d - 1)
        trends.append({
            "date": date.strftime('%Y-%m-%d'),
            "reports_filed": 30 + (d * 3) + (d % 3) * 5,
            "tasks_completed": 25 + (d * 2) + (d % 4) * 3,
            "avg_severity": round(4.5 + (d % 3) * 0.5, 1)
        })
    return trends


def get_worker_leaderboard(limit=10):
    """Top workers by completed tasks"""
    workers = [
        {"worker_id": f"W-{i:03d}", "name": f"Worker {i}", 
         "completed_this_week": max(1, 20 - i * 2 + (i % 3)),
         "avg_rating": round(4.0 + (i % 5) * 0.15, 1),
         "avg_resolution_hours": round(3.0 + i * 0.5, 1)}
        for i in range(1, limit + 1)
    ]
    return sorted(workers, key=lambda w: w['completed_this_week'], reverse=True)


def get_recent_reports(limit=10):
    """Latest reports for the dashboard feed"""
    return [
        {
            "report_id": "RPT-260228-XYZ",
            "category": "garbage_pile",
            "severity_score": 7,
            "ward_number": 15,
            "status": "in_progress",
            "created_at": "2026-02-28T09:30:00Z",
            "description": "Large garbage accumulation near apartment complex"
        },
        {
            "report_id": "RPT-260228-ABC",
            "category": "stagnant_water",
            "severity_score": 8,
            "ward_number": 3,
            "status": "pending",
            "created_at": "2026-02-28T08:15:00Z",
            "description": "Stagnant water pooling near children's playground"
        },
        {
            "report_id": "RPT-260227-DEF",
            "category": "blocked_sewer",
            "severity_score": 6,
            "ward_number": 22,
            "status": "completed",
            "created_at": "2026-02-27T16:45:00Z",
            "description": "Sewer blockage causing street flooding"
        }
    ]


def handler(event, context):
    """
    Lambda handler for dashboard data.
    
    GET /dashboard                → full dashboard data (all sections)
    GET /dashboard/stats          → overview numbers only
    GET /dashboard/heatmap        → ward heatmap data
    GET /dashboard/trends?days=7  → trend data
    GET /dashboard/leaderboard    → worker leaderboard
    GET /dashboard/recent         → recent reports feed
    """
    try:
        path = event.get('path', '/dashboard')
        query_params = event.get('queryStringParameters') or {}

        if path.endswith('/stats'):
            result = get_overview_stats()
        elif path.endswith('/heatmap'):
            result = get_ward_heatmap()
        elif path.endswith('/trends'):
            days = int(query_params.get('days', 7))
            result = get_trend_data(days)
        elif path.endswith('/leaderboard'):
            result = get_worker_leaderboard()
        elif path.endswith('/recent'):
            result = get_recent_reports()
        else:
            # Full dashboard — combine all sections
            result = {
                "stats": get_overview_stats(),
                "categories": get_category_breakdown(),
                "heatmap": get_ward_heatmap(),
                "trends": get_trend_data(7),
                "leaderboard": get_worker_leaderboard(5),
                "recent_reports": get_recent_reports(5),
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
    # Test: Full dashboard
    test_event = {"path": "/dashboard", "queryStringParameters": {}}
    result = handler(test_event, None)
    data = json.loads(result["body"])
    
    stats = data['stats']
    print("=== SanitiSense Dashboard ===")
    print(f"Total Reports: {stats['total_reports']}")
    print(f"Today: {stats['reports_today']} new | {stats['completed_today']} resolved")
    print(f"Pending: {stats['pending_tasks']} | In Progress: {stats['in_progress_tasks']}")
    print(f"AI Accuracy: {stats['ai_accuracy']}%")
    print(f"\nCategories: {len(data['categories'])}")
    print(f"Wards: {len(data['heatmap'])}")
    print(f"Trend days: {len(data['trends'])}")
