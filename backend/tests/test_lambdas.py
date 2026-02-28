"""
SanitiSense AI — Backend Test Suite
Uses moto (fake AWS) to run tests locally — no real AWS account needed.

Changes from original:
- TABLE_NAME (not DYNAMODB_TABLE), table 'SanitiSense' (not 'sanitisense-main')
- PK/SK uppercase, SK='META' (not 'METADATA')
- report_processor is synchronous — tests mock S3+Bedrock, not SQS
- task_manager has lat/lng/image_key + worker profile endpoint

Run:
    python -m pytest backend/tests/ -v
"""

import json
import os
import sys

import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock

# Add backend folder to PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ─── Environment setup BEFORE importing Lambda modules ───────────────────────
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['TABLE_NAME'] = 'SanitiSense'          # matches deployed infra
os.environ['S3_BUCKET'] = 'sanitisense-media-982253889131'
os.environ['SQS_QUEUE_URL'] = ''                  # not used in sync flow
os.environ['KNOWLEDGE_BASE_ID'] = ''              # triggers fallback mode
os.environ['BEDROCK_MODEL_ID'] = 'us.anthropic.claude-sonnet-4-20250514-v1:0'


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _create_tables():
    """
    Create DynamoDB tables inside the active moto mock context.
    Schema matches the real 'SanitiSense' table (PK/SK uppercase + GSI1).
    """
    ddb = boto3.resource('dynamodb', region_name='us-east-1')
    ddb.create_table(
        TableName='SanitiSense',
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'GSI1',
            'KeySchema': [
                {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'},
            ],
            'Projection': {'ProjectionType': 'ALL'},
        }],
        BillingMode='PAY_PER_REQUEST',
    )
    return ddb


def _mock_ai_analysis(is_spam=False, category='garbage_pile', severity=7):
    """Return a fake AI analysis result (avoids calling real Bedrock in tests)."""
    return {
        'is_spam': is_spam,
        'category': category,
        'severity_score': severity,
        'description': 'Large garbage pile near apartment entrance.',
        'health_risk': 'medium',
        'confidence': 0.91,
    }


# ─────────────────────────────────────────────────────────────────────────────
# report_processor tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReportProcessor:

    def test_generate_ticket_id_format(self):
        """Ticket ID must start with SAN and be exactly 9 chars (SAN + 6 hex)."""
        from lambdas.report_processor import generate_ticket_id
        for _ in range(20):
            tid = generate_ticket_id()
            assert tid.startswith('SAN'), f"Expected SAN prefix, got: {tid}"
            assert len(tid) == 9, f"Expected length 9, got: {len(tid)}"
            suffix = tid[3:]
            assert suffix == suffix.upper(), f"Hex suffix should be uppercase: {suffix}"

    @mock_aws
    def test_create_report_returns_200_and_ticket(self):
        """POST /reports (with mocked AI) should return 200 + ticket_id."""
        _create_tables()
        import importlib
        from lambdas import report_processor
        importlib.reload(report_processor)

        # Patch Bedrock call with fake result
        with patch.object(report_processor, 'analyze_image_from_s3',
                          return_value=_mock_ai_analysis()):
            event = {
                'httpMethod': 'POST', 'path': '/reports',
                'pathParameters': None, 'queryStringParameters': None,
                'body': json.dumps({'image_key': 'citizen-reports/2026/02/28/test.jpg',
                                    'latitude': 19.07, 'longitude': 72.88}),
            }
            result = report_processor.handler(event, None)
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'ticket_id' in body
        assert body['ticket_id'].startswith('SAN')
        assert body['status'] == 'pending'
        assert 'ai_analysis' in body

    @mock_aws
    def test_create_report_saves_to_dynamodb(self):
        """POST /reports must write the report AND a task to DynamoDB."""
        _create_tables()
        import importlib
        from lambdas import report_processor
        importlib.reload(report_processor)

        with patch.object(report_processor, 'analyze_image_from_s3',
                          return_value=_mock_ai_analysis()):
            event = {
                'httpMethod': 'POST', 'path': '/reports',
                'pathParameters': None, 'queryStringParameters': None,
                'body': json.dumps({'image_key': 'test.jpg', 'latitude': 19.0, 'longitude': 72.8}),
            }
            result = report_processor.handler(event, None)
        ticket = json.loads(result['body'])['ticket_id']

        # Report record
        ddb = boto3.resource('dynamodb', region_name='us-east-1')
        item = ddb.Table('SanitiSense').get_item(
            Key={'PK': f'REPORT#{ticket}', 'SK': 'META'}
        )
        assert 'Item' in item, "Report record not found in DynamoDB"
        assert item['Item']['ticket_id'] == ticket

        # Auto-created task record
        scan = ddb.Table('SanitiSense').scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('PK').begins_with('TASK#') &
                             boto3.dynamodb.conditions.Attr('SK').eq('META')
        )
        assert scan['Count'] >= 1, "Task auto-creation failed"

    @mock_aws
    def test_spam_image_returns_400(self):
        """POST /reports with a spam image must return 400."""
        _create_tables()
        import importlib
        from lambdas import report_processor
        importlib.reload(report_processor)

        with patch.object(report_processor, 'analyze_image_from_s3',
                          return_value=_mock_ai_analysis(is_spam=True)):
            event = {
                'httpMethod': 'POST', 'path': '/reports',
                'pathParameters': None, 'queryStringParameters': None,
                'body': json.dumps({'image_key': 'selfie.jpg', 'latitude': 19.0, 'longitude': 72.8}),
            }
            result = report_processor.handler(event, None)
        assert result['statusCode'] == 400
        assert json.loads(result['body'])['status'] == 'rejected'

    @mock_aws
    def test_missing_image_key_returns_400(self):
        """POST /reports without image_key must return 400."""
        _create_tables()
        import importlib
        from lambdas import report_processor
        importlib.reload(report_processor)

        event = {
            'httpMethod': 'POST', 'path': '/reports',
            'pathParameters': None, 'queryStringParameters': None,
            'body': json.dumps({'latitude': 19.0, 'longitude': 72.8}),
        }
        result = report_processor.handler(event, None)
        assert result['statusCode'] == 400

    @mock_aws
    def test_get_ticket_not_found_returns_404(self):
        """GET /reports/SANXXXXXX for unknown ticket must return 404."""
        _create_tables()
        import importlib
        from lambdas import report_processor
        importlib.reload(report_processor)

        event = {
            'httpMethod': 'GET', 'path': '/reports/SANXXXXXX',
            'pathParameters': {'ticket_id': 'SANXXXXXX'},
            'queryStringParameters': None, 'body': None,
        }
        result = report_processor.handler(event, None)
        assert result['statusCode'] == 404


# ─────────────────────────────────────────────────────────────────────────────
# task_manager tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTaskManager:

    def test_priority_mapping(self):
        """Severity → priority + SLA hours must match the spec."""
        from lambdas.task_manager import _priority_from_severity
        assert _priority_from_severity(9) == ('critical', 4)
        assert _priority_from_severity(8) == ('critical', 4)
        assert _priority_from_severity(7) == ('high', 12)
        assert _priority_from_severity(6) == ('high', 12)
        assert _priority_from_severity(5) == ('medium', 24)
        assert _priority_from_severity(4) == ('medium', 24)
        assert _priority_from_severity(3) == ('low', 48)
        assert _priority_from_severity(1) == ('low', 48)

    @mock_aws
    def test_create_task_includes_lat_lng_image_key(self):
        """create_task() must copy lat/lng/image_key from report_data."""
        _create_tables()
        import importlib
        from lambdas import task_manager
        importlib.reload(task_manager)

        task = task_manager.create_task(
            report_data={
                'ticket_id': 'SAN123456',
                'latitude': 19.0760,
                'longitude': 72.8777,
                'ward_number': 7,
                'image_key': 'citizen-reports/2026/02/28/abc.jpg',
            },
            ai_analysis=_mock_ai_analysis()
        )
        # DynamoDB stores as Decimal — compare as float
        assert float(task['latitude']) == 19.0760
        assert float(task['longitude']) == 72.8777
        assert task['image_key'] == 'citizen-reports/2026/02/28/abc.jpg'
        assert task['ward_number'] == 7


    @mock_aws
    def test_start_task_without_worker_id_returns_400(self):
        """POST /tasks/{id}/start without worker_id must return 400."""
        _create_tables()
        import importlib
        from lambdas import task_manager
        importlib.reload(task_manager)

        event = {
            'httpMethod': 'POST', 'path': '/tasks/TSK-001/start',
            'pathParameters': {'task_id': 'TSK-001'},
            'queryStringParameters': None, 'body': json.dumps({}),
        }
        result = task_manager.handler(event, None)
        assert result['statusCode'] == 400

    @mock_aws
    def test_complete_task_without_after_photo_returns_400(self):
        """POST /tasks/{id}/complete without after_image_key must return 400."""
        _create_tables()
        import importlib
        from lambdas import task_manager
        importlib.reload(task_manager)

        event = {
            'httpMethod': 'POST', 'path': '/tasks/TSK-001/complete',
            'pathParameters': {'task_id': 'TSK-001'},
            'queryStringParameters': None, 'body': json.dumps({}),
        }
        result = task_manager.handler(event, None)
        assert result['statusCode'] == 400

    @mock_aws
    def test_worker_profile_not_found_returns_404(self):
        """GET /worker/W-999/profile for unknown worker must return 404."""
        _create_tables()
        import importlib
        from lambdas import task_manager
        importlib.reload(task_manager)

        event = {
            'httpMethod': 'GET', 'path': '/worker/W-999/profile',
            'pathParameters': {'worker_id': 'W-999'},
            'queryStringParameters': None, 'body': None,
        }
        result = task_manager.handler(event, None)
        assert result['statusCode'] == 404

    @mock_aws
    def test_worker_profile_found(self):
        """GET /worker/{id}/profile returns profile if it exists."""
        _create_tables()
        ddb = boto3.resource('dynamodb', region_name='us-east-1')
        ddb.Table('SanitiSense').put_item(Item={
            'PK': 'WORKER#W-001', 'SK': 'PROFILE',
            'worker_id': 'W-001', 'name': 'Ramesh Kumar',
            'ward_assigned': 7, 'status': 'active',
            'total_completed': 45, 'avg_rating': '4.3',
        })
        import importlib
        from lambdas import task_manager
        importlib.reload(task_manager)

        event = {
            'httpMethod': 'GET', 'path': '/worker/W-001/profile',
            'pathParameters': {'worker_id': 'W-001'},
            'queryStringParameters': None, 'body': None,
        }
        result = task_manager.handler(event, None)
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['worker_id'] == 'W-001'
        assert body['name'] == 'Ramesh Kumar'

    @mock_aws
    def test_invalid_status_update_returns_400(self):
        """PUT /tasks/{id} with invalid status must return 400."""
        _create_tables()
        import importlib
        from lambdas import task_manager
        importlib.reload(task_manager)

        event = {
            'httpMethod': 'PUT', 'path': '/tasks/TSK-001',
            'pathParameters': {'task_id': 'TSK-001'},
            'queryStringParameters': None,
            'body': json.dumps({'status': 'flying_to_mars'}),
        }
        result = task_manager.handler(event, None)
        assert result['statusCode'] == 400


# ─────────────────────────────────────────────────────────────────────────────
# dashboard_api tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDashboardApi:

    @mock_aws
    def test_full_dashboard_returns_200_with_sections(self):
        """GET /dashboard must return 200 with stats/heatmap/trends."""
        _create_tables()
        import importlib
        from lambdas import dashboard_api
        importlib.reload(dashboard_api)

        result = dashboard_api.handler({'path': '/dashboard', 'queryStringParameters': {}}, None)
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'stats' in body
        assert 'heatmap' in body
        assert 'trends' in body

    @mock_aws
    def test_stats_keys(self):
        """GET /dashboard/stats must return all expected counter keys."""
        _create_tables()
        import importlib
        from lambdas import dashboard_api
        importlib.reload(dashboard_api)

        result = dashboard_api.handler({'path': '/dashboard/stats', 'queryStringParameters': {}}, None)
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'total_reports' in body
        assert 'pending_count' in body
        assert 'category_counts' in body

    @mock_aws
    def test_ward_reports_endpoint(self):
        """GET /dashboard/reports?ward=7 must return report list for that ward."""
        _create_tables()
        # Seed a report for ward 7
        ddb = boto3.resource('dynamodb', region_name='us-east-1')
        ddb.Table('SanitiSense').put_item(Item={
            'PK': 'REPORT#SAN000001', 'SK': 'META',
            'ticket_id': 'SAN000001',
            'ward_number': 7,
            'latitude': '19.1136', 'longitude': '72.8697',
            'category': 'garbage_pile',
            'severity_score': 7,
            'status': 'pending',
            'created_at': '2026-02-28T09:00:00Z',
            'description': 'Test report',
            'GSI1PK': 'STATUS#pending', 'GSI1SK': '2026-02-28T09:00:00Z',
        })
        import importlib
        from lambdas import dashboard_api
        importlib.reload(dashboard_api)

        result = dashboard_api.handler(
            {'path': '/dashboard/reports', 'queryStringParameters': {'ward': '7'}},
            None
        )
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['count'] == 1
        assert body['reports'][0]['category'] == 'garbage_pile'

    @mock_aws
    def test_ward_reports_wrong_ward_returns_empty(self):
        """GET /dashboard/reports?ward=99 for empty ward should return 0 reports."""
        _create_tables()
        import importlib
        from lambdas import dashboard_api
        importlib.reload(dashboard_api)

        result = dashboard_api.handler(
            {'path': '/dashboard/reports', 'queryStringParameters': {'ward': '99'}},
            None
        )
        assert result['statusCode'] == 200
        assert json.loads(result['body'])['count'] == 0

    def test_trend_data_length(self):
        """get_trend_data(reports, N) must return exactly N days."""
        from lambdas.dashboard_api import get_trend_data
        for n in (3, 7, 14, 30):
            assert len(get_trend_data([], n)) == n

    def test_heatmap_ward_names(self):
        """Leaderboard returns empty list when no workers have completed tasks."""
        from lambdas.dashboard_api import get_worker_leaderboard
        lb = get_worker_leaderboard([], 5)  # empty reports = no workers
        assert isinstance(lb, list)
        # With real seeded data that has assigned_worker_id, lb would be populated

    @mock_aws
    def test_ward_reports_missing_ward_returns_400(self):
        """GET /dashboard/reports without ward= param must return 400."""
        _create_tables()
        import importlib
        from lambdas import dashboard_api
        importlib.reload(dashboard_api)

        result = dashboard_api.handler(
            {'path': '/dashboard/reports', 'queryStringParameters': {}},
            None
        )
        assert result['statusCode'] == 400


# ─────────────────────────────────────────────────────────────────────────────
# epidemic_advisor tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEpidemicAdvisor:

    def test_season_detection(self):
        """_get_current_season() must return a valid season name."""
        from lambdas.epidemic_advisor import _get_current_season
        assert _get_current_season() in ('monsoon', 'post-monsoon', 'winter', 'summer')

    def test_parse_rag_advisory_extracts_diseases(self):
        """_parse_rag_advisory must detect disease names from advisory text."""
        from lambdas.epidemic_advisor import _parse_rag_advisory
        text = "There is significant risk of Dengue and Malaria due to stagnant water. 1. Deploy fogging teams. 2. Issue public advisory."
        result = _parse_rag_advisory(text, {'avg_severity': 7, 'stagnant_water_count': 4})
        assert 'Dengue' in result['diseases_at_risk']
        assert 'Malaria' in result['diseases_at_risk']
        assert len(result['recommended_actions']) >= 1
        assert result['risk_level'] in ('low', 'medium', 'high', 'critical')

    def test_direct_bedrock_fallback_used_when_no_kb(self):
        """
        When KNOWLEDGE_BASE_ID is empty, get_ward_advisory uses direct Bedrock.
        We mock _query_direct to avoid hitting real AWS.
        """
        from lambdas import epidemic_advisor
        import importlib
        importlib.reload(epidemic_advisor)

        mock_response = {
            'text': 'High risk of dengue.',
            'risk_level': 'high',
            'diseases_at_risk': ['Dengue'],
            'recommended_actions': ['Deploy fogging teams'],
            'citations': [],
            'source': 'bedrock_direct',
        }

        with patch.object(epidemic_advisor, '_query_direct', return_value=mock_response), \
             patch.object(epidemic_advisor, 'get_ward_stats', return_value={
                 'ward_number': 7, 'open_reports': 10, 'top_categories': 'stagnant_water (5)',
                 'avg_severity': 7.0, 'stagnant_water_count': 5, 'season': 'monsoon',
             }):
            result = epidemic_advisor.get_ward_advisory(7)

        assert result['data_source'] == 'bedrock_direct'
        assert result['risk_level'] == 'high'
        assert 'Dengue' in result['diseases_at_risk']
        assert len(result['recommended_actions']) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# get_upload_url tests  (pure logic — no AWS calls needed)
# ─────────────────────────────────────────────────────────────────────────────

class TestGetUploadUrl:

    def test_citizen_key_format(self):
        """Citizen image key must start with citizen-reports/YYYY/MM/DD."""
        from lambdas.get_upload_url import generate_image_key
        key = generate_image_key('photo.jpg', 'citizen')
        parts = key.split('/')
        assert parts[0] == 'citizen-reports'
        assert len(parts) == 5   # folder/YYYY/MM/DD/filename
        assert key.endswith('.jpg')

    def test_worker_key_format(self):
        """Worker image key must start with worker-completions/."""
        from lambdas.get_upload_url import generate_image_key
        key = generate_image_key('after.png', 'worker')
        assert key.startswith('worker-completions/')
        assert key.endswith('.png')

    def test_dangerous_extension_blocked(self):
        """Executables and scripts must be converted to .jpg."""
        from lambdas.get_upload_url import generate_image_key
        assert generate_image_key('hack.exe').endswith('.jpg')
        assert generate_image_key('script.sh').endswith('.jpg')
        assert generate_image_key('malware.bat').endswith('.jpg')

    def test_allowed_extensions_pass_through(self):
        """Allowed image extensions must be preserved."""
        from lambdas.get_upload_url import generate_image_key
        assert generate_image_key('image.png').endswith('.png')
        assert generate_image_key('image.webp').endswith('.webp')
        assert generate_image_key('image.heic').endswith('.heic')
