"""
SanitiSense AI — Task Manager Lambda
Worker task CRUD + worker profile lookup.

Trigger: API Gateway
  GET  /tasks?status=X               → list tasks by status (uses GSI1)
  GET  /tasks?worker_id=W-001        → list tasks for a specific worker
  GET  /worker/{worker_id}/tasks     → same as above (path param version, deployed in SAM)
  POST /tasks                         → create task from report + AI analysis
  POST /tasks/{task_id}/start         → worker starts a task → status: in_progress
  POST /tasks/{task_id}/complete      → worker submits after-photo → status: completed
  PUT  /tasks/{task_id}               → generic status update (admin use)
  GET  /worker/{worker_id}/profile    → worker profile for login verification

DynamoDB schema (matches the deployed SanitiSense table):
  PK = TASK#{task_id}    SK = META
  PK = WORKER#{id}       SK = PROFILE   (for worker profiles)
  GSI1PK = STATUS#{status}   GSI1SK = {created_at}
"""

import json
import os
import uuid
from datetime import datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

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


def _now() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def _find_task_key(task_id: str) -> dict:
    """Find the DynamoDB key for a task, regardless of PK format.
    Seed data uses PK=REPORT#, create_task() uses PK=TASK#."""
    # Try TASK# first (new records)
    resp = table.get_item(Key={'PK': f'TASK#{task_id}', 'SK': 'META'})
    if 'Item' in resp:
        return {'PK': f'TASK#{task_id}', 'SK': 'META'}
    # Fallback: scan for task_id field (seed data uses REPORT# prefix)
    # NOTE: Do NOT use Limit here — DynamoDB Limit caps items *evaluated*,
    # not items *matched*, so Limit=1 almost never finds the right record.
    resp = table.scan(
        FilterExpression=Attr('task_id').eq(task_id) & Attr('SK').eq('META'),
    )
    items = resp.get('Items', [])
    if items:
        return {'PK': items[0]['PK'], 'SK': 'META'}
    raise ValueError(f'Task {task_id} not found')


def _priority_from_severity(severity: int) -> tuple:
    """Returns (priority_label, sla_hours)."""
    if severity >= 8:
        return 'critical', 4
    elif severity >= 6:
        return 'high', 12
    elif severity >= 4:
        return 'medium', 24
    return 'low', 48


# ─────────────────────────────────────────────────────────────────────────────
# POST /tasks — Create task from report + AI analysis
# ─────────────────────────────────────────────────────────────────────────────

def create_task(report_data: dict, ai_analysis: dict) -> dict:
    """
    Create a new task record. Copies lat/lng/image_key from the report
    so the worker can see the location on a map and the before-photo.
    """
    task_id = f"TSK-{datetime.utcnow().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now = _now()
    severity = ai_analysis.get('severity_score', 5)
    priority, sla_hours = _priority_from_severity(severity)

    lat = report_data.get('latitude', 0)
    lng = report_data.get('longitude', 0)

    task = {
        'PK': f'TASK#{task_id}',
        'SK': 'META',
        'task_id': task_id,
        'report_ticket': report_data.get('ticket_id', ''),
        # ── Fields the frontend needs for map + validation ─────────────────
        'image_key': report_data.get('image_key', ''),     # before-photo
        'after_image_key': '',
        'latitude': Decimal(str(round(float(lat), 6))),    # Decimal required by DynamoDB
        'longitude': Decimal(str(round(float(lng), 6))),
        'ward_number': int(report_data.get('ward_number', 0)),
        # ── AI classification ──────────────────────────────────────────────
        'status': 'pending',
        'priority': priority,
        'sla_hours': sla_hours,
        'category': ai_analysis.get('category', 'other'),
        'severity_score': severity,
        'health_risk': ai_analysis.get('health_risk', 'low'),
        'description': ai_analysis.get('description', ''),
        # ── Assignment ─────────────────────────────────────────────────────
        'assigned_worker_id': None,
        'worker_notes': '',
        'created_at': now,
        'updated_at': now,
        'GSI1PK': 'STATUS#pending',
        'GSI1SK': now,
    }
    table.put_item(Item=task)
    return task


# ─────────────────────────────────────────────────────────────────────────────
# GET /tasks?status=X — list by status via GSI1
# ─────────────────────────────────────────────────────────────────────────────

def get_tasks_by_status(status: str, limit: int = 20) -> list:
    """Query all tasks with a given status. Newest first."""
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq(f'STATUS#{status}'),
        Limit=limit,
        ScanIndexForward=False,
    )
    return response.get('Items', [])


# ─────────────────────────────────────────────────────────────────────────────
# GET /worker/{worker_id}/tasks — tasks assigned to a worker
# ─────────────────────────────────────────────────────────────────────────────

def get_worker_tasks(worker_id: str) -> list:
    """
    Get all tasks assigned to a specific worker.
    Scan with filter on assigned_worker_id — fine at current data volume.
    For scale: Person C should add a GSI on assigned_worker_id.
    """
    response = table.scan(
        FilterExpression=(
            Attr('assigned_worker_id').eq(worker_id) &
            Attr('SK').eq('META') &
            Attr('PK').begins_with('TASK#')
        )
    )
    items = response.get('Items', [])
    # Sort by priority so most urgent tasks appear first
    order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    return sorted(items, key=lambda t: order.get(t.get('priority', 'low'), 9))


# ─────────────────────────────────────────────────────────────────────────────
# Helper: mirror task status back to the parent REPORT item
# ─────────────────────────────────────────────────────────────────────────────

def _sync_report_status(report_ticket: str, new_status: str, now: str) -> None:
    """
    Update the parent REPORT item's status so the /track citizen page
    always reflects reality. Silently swallows errors — task update
    must not fail just because the linked report can't be found.
    """
    if not report_ticket:
        return
    try:
        table.update_item(
            Key={'PK': f'REPORT#{report_ticket}', 'SK': 'META'},
            UpdateExpression='SET #st = :s, updated_at = :t, GSI1PK = :gsi',
            ConditionExpression='attribute_exists(PK)',
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':s': new_status,
                ':t': now,
                ':gsi': f'STATUS#{new_status}',
            },
        )
        print(f'[SYNC] Report {report_ticket} → {new_status}')
    except Exception as e:
        print(f'[WARN] Could not sync report {report_ticket} status: {e}')


# ─────────────────────────────────────────────────────────────────────────────
# POST /tasks/{task_id}/start — worker starts working
# ─────────────────────────────────────────────────────────────────────────────

def start_task(task_id: str, worker_id: str) -> dict:
    """Assign task to worker and set status to in_progress."""
    now = _now()
    key = _find_task_key(task_id)
    # Read item FIRST so we can grab report_ticket for status sync
    task_item = table.get_item(Key=key).get('Item', {})
    table.update_item(
        Key=key,
        UpdateExpression=(
            'SET #st = :s, assigned_worker_id = :w, '
            'updated_at = :t, started_at = :t, GSI1PK = :gsi'
        ),
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues={
            ':s': 'in_progress',
            ':w': worker_id,
            ':t': now,
            ':gsi': 'STATUS#in_progress',
        }
    )
    _sync_report_status(task_item.get('report_ticket', ''), 'in_progress', now)
    return {'task_id': task_id, 'status': 'in_progress', 'worker_id': worker_id}


# ─────────────────────────────────────────────────────────────────────────────
# POST /tasks/{task_id}/complete — worker submits after-photo
# ─────────────────────────────────────────────────────────────────────────────

def complete_task(task_id: str, after_image_key: str, worker_notes: str = '') -> dict:
    """
    Worker has finished cleanup and uploaded an after-photo.
    Saves the after_image_key so the validation Lambda can compare before/after.
    """
    now = _now()
    key = _find_task_key(task_id)
    task_item = table.get_item(Key=key).get('Item', {})
    table.update_item(
        Key=key,
        UpdateExpression=(
            'SET #st = :s, after_image_key = :after, '
            'worker_notes = :notes, completed_at = :t, '
            'updated_at = :t, GSI1PK = :gsi'
        ),
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues={
            ':s': 'completed',
            ':after': after_image_key,
            ':notes': worker_notes,
            ':t': now,
            ':gsi': 'STATUS#completed',
        }
    )
    _sync_report_status(task_item.get('report_ticket', ''), 'completed', now)
    return {
        'task_id': task_id,
        'status': 'completed',
        'after_image_key': after_image_key,
        'message': 'Task marked complete. AI validation will run shortly.',
    }


# ─────────────────────────────────────────────────────────────────────────────
# PUT /tasks/{task_id} — generic status update
# ─────────────────────────────────────────────────────────────────────────────

def update_task_status(task_id: str, new_status: str, notes: str = '', worker_id: str = '') -> dict:
    valid = {'pending', 'assigned', 'in_progress', 'completed', 'verified', 'rejected'}
    if new_status not in valid:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of: {sorted(valid)}")

    now = _now()
    key = _find_task_key(task_id)
    task_item = table.get_item(Key=key).get('Item', {})

    update_expr = 'SET #st = :s, updated_at = :t, worker_notes = :n, GSI1PK = :gsi'
    expr_values = {
        ':s': new_status,
        ':t': now,
        ':n': notes,
        ':gsi': f'STATUS#{new_status}',
    }
    # Save the worker ID if provided and not already set
    if worker_id and not task_item.get('assigned_worker_id'):
        update_expr += ', assigned_worker_id = :w'
        expr_values[':w'] = worker_id

    table.update_item(
        Key=key,
        UpdateExpression=update_expr,
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues=expr_values,
    )
    _sync_report_status(task_item.get('report_ticket', ''), new_status, now)
    return {'task_id': task_id, 'status': new_status, 'updated_at': now}


# ─────────────────────────────────────────────────────────────────────────────
# GET /worker/{worker_id}/profile — worker profile for login
# ─────────────────────────────────────────────────────────────────────────────

def get_worker_profile(worker_id: str) -> dict | None:
    """
    Fetch worker profile from DynamoDB.
    PK = WORKER#{worker_id}   SK = PROFILE
    Returns None if not found (frontend shows 404).
    """
    response = table.get_item(
        Key={'PK': f'WORKER#{worker_id}', 'SK': 'PROFILE'}
    )
    return response.get('Item')


# ─────────────────────────────────────────────────────────────────────────────
# Main handler
# ─────────────────────────────────────────────────────────────────────────────

def handler(event, context):
    try:
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/tasks')
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}

        task_id = path_params.get('task_id', '')
        worker_id = path_params.get('worker_id', '')

        # GET /worker/{worker_id}/profile
        if method == 'GET' and worker_id and path.endswith('/profile'):
            profile = get_worker_profile(worker_id)
            if profile is None:
                return _response(404, {'error': f'Worker {worker_id} not found'})
            return _response(200, profile)

        # GET /worker/{worker_id}/tasks  (path-param version — SAM route)
        elif method == 'GET' and worker_id and path.endswith('/tasks'):
            tasks = get_worker_tasks(worker_id)
            return _response(200, {'tasks': tasks, 'count': len(tasks)})

        # POST /tasks/{id}/start
        elif method == 'POST' and task_id and path.endswith('/start'):
            wid = body.get('worker_id', '')
            if not wid:
                return _response(400, {'error': 'worker_id is required'})
            result = start_task(task_id, wid)
            return _response(200, result)

        # POST /tasks/{id}/complete
        elif method == 'POST' and task_id and path.endswith('/complete'):
            after_key = body.get('after_image_key', '')
            if not after_key:
                return _response(400, {'error': 'after_image_key is required'})
            result = complete_task(task_id, after_key, body.get('worker_notes', ''))
            return _response(200, result)

        # POST /tasks — create task
        elif method == 'POST' and path.rstrip('/') == '/tasks':
            result = create_task(body.get('report_data', {}), body.get('ai_analysis', {}))
            return _response(200, result)

        # GET /tasks?worker_id=xxx  (query-param version)
        elif method == 'GET' and query_params.get('worker_id'):
            tasks = get_worker_tasks(query_params['worker_id'])
            return _response(200, {'tasks': tasks, 'count': len(tasks)})

        # GET /tasks?status=xxx
        elif method == 'GET' and '/tasks' in path:
            status = query_params.get('status', 'pending')
            limit = min(int(query_params.get('limit', 20)), 100)
            tasks = get_tasks_by_status(status, limit)
            return _response(200, {'tasks': tasks, 'count': len(tasks)})

        # PUT /tasks/{id}
        elif method == 'PUT' and task_id:
            result = update_task_status(
                task_id,
                body.get('status', ''),
                body.get('notes', ''),
                body.get('worker_id', ''),
            )
            return _response(200, result)

        return _response(404, {'error': 'Route not found'})

    except ValueError as e:
        return _response(400, {'error': str(e)})
    except Exception as e:
        return _response(500, {'error': str(e)})


# ─── Local smoke test ────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Testing _priority_from_severity()...")
    assert _priority_from_severity(9) == ('critical', 4)
    assert _priority_from_severity(6) == ('high', 12)
    assert _priority_from_severity(4) == ('medium', 24)
    assert _priority_from_severity(2) == ('low', 48)
    print("  ✓ All priority mappings correct")
    print("\nSmoke tests passed. Full handler requires AWS DynamoDB.")
