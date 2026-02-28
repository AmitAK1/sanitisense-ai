"""
SanitiSense AI — Task Manager Lambda
Handles worker task assignment, status updates, and task queries.
Uses DynamoDB single-table design.
"""

import json
import os
import uuid
from datetime import datetime

import boto3
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SanitiSense'))

TABLE_NAME = os.environ.get('TABLE_NAME', 'SanitiSense')

# ========== DynamoDB KEY PATTERNS ==========
# PK: TASK#<task_id>          SK: META
# PK: WORKER#<worker_id>      SK: TASK#<task_id>
# PK: WARD#<ward_number>      SK: TASK#<task_id>
# GSI1PK: STATUS#<status>     GSI1SK: <created_at>


def create_task(report_data, ai_analysis):
    """
    Create a new task from a citizen report + AI analysis.
    Auto-assigns priority based on severity score.
    """
    task_id = f"TSK-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.utcnow().isoformat() + 'Z'
    
    # Priority mapping from severity
    severity = ai_analysis.get('severity_score', 5)
    if severity >= 8:
        priority = 'critical'
        sla_hours = 4
    elif severity >= 6:
        priority = 'high'
        sla_hours = 12
    elif severity >= 4:
        priority = 'medium'
        sla_hours = 24
    else:
        priority = 'low'
        sla_hours = 48

    task = {
        'PK': f'TASK#{task_id}',
        'SK': 'META',
        'task_id': task_id,
        'report_id': report_data.get('report_id', ''),
        'status': 'pending',
        'priority': priority,
        'sla_hours': sla_hours,
        'category': ai_analysis.get('category', 'other'),
        'severity_score': severity,
        'location': report_data.get('location', {}),
        'ward_number': report_data.get('ward_number', 0),
        'description': ai_analysis.get('description', ''),
        'assigned_worker_id': None,
        'created_at': now,
        'updated_at': now,
        # GSI1 for querying by status
        'GSI1PK': 'STATUS#pending',
        'GSI1SK': now
    }

    table.put_item(Item=task)
    
    return task


def assign_task(task_id, worker_id):
    """Assign a task to a worker"""
    now = datetime.utcnow().isoformat() + 'Z'
    
    table.update_item(
        Key={'PK': f'TASK#{task_id}', 'SK': 'META'},
        UpdateExpression='SET #s = :s, assigned_worker_id = :w, updated_at = :t, GSI1PK = :gsi',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':s': 'assigned',
            ':w': worker_id,
            ':t': now,
            ':gsi': 'STATUS#assigned'
        }
    )
    
    return {"task_id": task_id, "worker_id": worker_id, "status": "assigned"}


def update_task_status(task_id, new_status, worker_notes=""):
    """Update task status (assigned, in_progress, completed, verified)"""
    now = datetime.utcnow().isoformat() + 'Z'
    
    valid_statuses = ['pending', 'assigned', 'in_progress', 'completed', 'verified', 'rejected']
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
    
    table.update_item(
        Key={'PK': f'TASK#{task_id}', 'SK': 'META'},
        UpdateExpression='SET #s = :s, updated_at = :t, worker_notes = :n, GSI1PK = :gsi',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':s': new_status,
            ':t': now,
            ':n': worker_notes,
            ':gsi': f'STATUS#{new_status}'
        }
    )
    
    return {"task_id": task_id, "status": new_status, "updated_at": now}


def get_tasks_by_status(status, limit=20):
    """Query tasks by status using GSI1"""
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :pk',
        ExpressionAttributeValues={':pk': f'STATUS#{status}'},
        Limit=limit,
        ScanIndexForward=False  # newest first
    )
    return response['Items']


def get_worker_tasks(worker_id):
    """Get all tasks assigned to a specific worker"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': f'WORKER#{worker_id}'}
    )
    return response['Items']


def handler(event, context):
    """
    Lambda handler for task management.
    Routes based on HTTP method + path.
    
    POST   /tasks          → create new task
    GET    /tasks?status=X → list tasks by status
    PUT    /tasks/{id}     → update task status
    GET    /worker/{id}/tasks → get worker's tasks
    """
    try:
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/tasks')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}

        if method == 'POST' and '/tasks' in path:
            # Create task from report + AI analysis
            result = create_task(
                body.get('report_data', {}),
                body.get('ai_analysis', {})
            )
        
        elif method == 'GET' and '/worker/' in path:
            worker_id = path_params.get('worker_id', '')
            result = get_worker_tasks(worker_id)
        
        elif method == 'GET' and '/tasks' in path:
            status = query_params.get('status', 'pending')
            result = get_tasks_by_status(status)
        
        elif method == 'PUT' and '/tasks/' in path:
            task_id = path_params.get('task_id', '')
            result = update_task_status(
                task_id,
                body.get('status', ''),
                body.get('notes', '')
            )
        
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Route not found"})
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
    # Test: Create task
    test_event = {
        "httpMethod": "POST",
        "path": "/tasks",
        "body": json.dumps({
            "report_data": {
                "report_id": "RPT-001",
                "ward_number": 42,
                "location": {"lat": 19.076, "lng": 72.877}
            },
            "ai_analysis": {
                "category": "garbage_pile",
                "severity_score": 7,
                "description": "Large garbage pile near school entrance"
            }
        })
    }
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
