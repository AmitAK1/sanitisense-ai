import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SanitiSense')

print('=== TASK items ===')
resp = table.scan(FilterExpression=Attr('PK').begins_with('TASK#') & Attr('SK').eq('META'))
tasks = resp.get('Items', [])
for t in tasks:
    print(f"  task_id={t.get('task_id')}  status={t.get('status')}  worker={t.get('assigned_worker_id')}  ticket={t.get('report_ticket')}")
print(f"  Total tasks: {len(tasks)}")

print()
print('=== WORKER profiles ===')
resp2 = table.scan(FilterExpression=Attr('PK').begins_with('WORKER#') & Attr('SK').eq('PROFILE'))
workers = resp2.get('Items', [])
for w in workers:
    print(f"  worker_id={w.get('worker_id')}  name={w.get('name')}  avg_rating={w.get('avg_rating')}  rating_count={w.get('rating_count')}")
if not workers:
    print('  (none found)')
