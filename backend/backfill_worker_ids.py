"""
One-time backfill: set assigned_worker_id = 'W-001' on all TASK items
where assigned_worker_id is missing or None.
Run once, safe to re-run (skips tasks that already have a worker).
"""
import boto3

TABLE = 'SanitiSense'
DEFAULT_WORKER = 'W-001'

dynamo = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamo.Table(TABLE)

def scan_tasks():
    items, last_key = [], None
    while True:
        kwargs = {'FilterExpression': 'begins_with(PK, :prefix)',
                  'ExpressionAttributeValues': {':prefix': 'TASK#'}}
        if last_key:
            kwargs['ExclusiveStartKey'] = last_key
        resp = table.scan(**kwargs)
        items.extend(resp.get('Items', []))
        last_key = resp.get('LastEvaluatedKey')
        if not last_key:
            break
    return items

tasks = scan_tasks()
print(f"Total TASK items found: {len(tasks)}")

updated = 0
skipped = 0
for task in tasks:
    pk, sk = task['PK'], task['SK']
    existing_worker = task.get('assigned_worker_id')
    if existing_worker:
        skipped += 1
        continue
    table.update_item(
        Key={'PK': pk, 'SK': sk},
        UpdateExpression='SET assigned_worker_id = :w',
        ExpressionAttributeValues={':w': DEFAULT_WORKER},
    )
    print(f"  Updated {task.get('task_id', pk)} → worker={DEFAULT_WORKER}")
    updated += 1

print(f"\nDone. Updated: {updated}  |  Already had worker: {skipped}")
