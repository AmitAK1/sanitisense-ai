"""Delete phantom TASK# records created by failed updates."""
import boto3
from boto3.dynamodb.conditions import Attr

table = boto3.resource('dynamodb', region_name='us-east-1').Table('SanitiSense')

resp = table.scan(FilterExpression=Attr('PK').begins_with('TASK#'))
items = resp.get('Items', [])
print(f'Found {len(items)} TASK# records to delete')

for item in items:
    pk, sk = item['PK'], item['SK']
    print(f'  Deleting {pk} / {sk} ...')
    table.delete_item(Key={'PK': pk, 'SK': sk})

print('Done — all phantom TASK# records removed')
