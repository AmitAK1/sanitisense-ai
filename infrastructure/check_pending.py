"""Check what the 'empty' pending records actually contain."""
import boto3
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb', region_name='us-east-1').Table('SanitiSense')
resp = table.query(
    IndexName='GSI1',
    KeyConditionExpression=Key('GSI1PK').eq('STATUS#pending'),
    ScanIndexForward=False,
)
for i, item in enumerate(resp['Items']):
    tid = item.get('task_id', 'MISSING')
    rid = item.get('report_id', 'MISSING')
    pk = item.get('PK', 'MISSING')
    print(f"[{i}] PK={pk}  task_id={tid}  report_id={rid}")
