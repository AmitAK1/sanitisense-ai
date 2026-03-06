"""
Redistribute tasks across all 5 workers so the leaderboard shows all workers.
Assigns tasks round-robin so each worker gets a fair share.
Safe to re-run.
"""
import boto3

TABLE = 'SanitiSense'
WORKERS = ['W-001', 'W-002', 'W-003', 'W-004', 'W-005']

dynamo = boto3.resource('dynamodb', region_name='us-east-1')
table  = dynamo.Table(TABLE)

# Scan all TASK items
items, last_key = [], None
while True:
    kwargs = {
        'FilterExpression': 'begins_with(PK, :p)',
        'ExpressionAttributeValues': {':p': 'TASK#'},
    }
    if last_key:
        kwargs['ExclusiveStartKey'] = last_key
    resp = table.scan(**kwargs)
    items.extend(resp.get('Items', []))
    last_key = resp.get('LastEvaluatedKey')
    if not last_key:
        break

print(f"Total TASK items: {len(items)}")

for i, task in enumerate(items):
    worker = WORKERS[i % len(WORKERS)]
    table.update_item(
        Key={'PK': task['PK'], 'SK': task['SK']},
        UpdateExpression='SET assigned_worker_id = :w',
        ExpressionAttributeValues={':w': worker},
    )
    print(f"  {task.get('task_id', task['PK'])} → {worker}")

print("\nDone! Tasks distributed across all workers.")
