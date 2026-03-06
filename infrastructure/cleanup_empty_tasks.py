"""Clean up phantom DynamoDB records that have no task_id or report_id."""
import boto3
from boto3.dynamodb.conditions import Attr

table = boto3.resource('dynamodb', region_name='us-east-1').Table('SanitiSense')
resp = table.scan(FilterExpression=Attr('SK').eq('META'))
phantoms = [i for i in resp['Items'] if not i.get('task_id') and not i.get('report_id')]
print(f'Found {len(phantoms)} phantom records')
for p in phantoms:
    pk = p['PK']
    print(f'  Deleting {pk}')
    table.delete_item(Key={'PK': pk, 'SK': 'META'})
print('Done')
