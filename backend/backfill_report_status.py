"""
One-time backfill: scan all TASK items that are NOT pending,
then update the linked REPORT item to match the task's status.

Run once from the backend/ directory:
  python backfill_report_status.py
"""
import os
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime

TABLE_NAME = 'SanitiSense'
REGION = 'us-east-1'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


def now():
    return datetime.utcnow().isoformat() + 'Z'


def main():
    print(f"Scanning TASK items in '{TABLE_NAME}'...")
    items = []
    params = {
        'FilterExpression': (
            Attr('PK').begins_with('TASK#') &
            Attr('SK').eq('META')
        )
    }
    while True:
        resp = table.scan(**params)
        items.extend(resp.get('Items', []))
        if 'LastEvaluatedKey' not in resp:
            break
        params['ExclusiveStartKey'] = resp['LastEvaluatedKey']

    print(f"  Found {len(items)} task(s) total")

    updated = 0
    skipped = 0
    for task in items:
        status = task.get('status', 'pending')
        report_ticket = task.get('report_ticket', '')

        if status == 'pending' or not report_ticket:
            skipped += 1
            continue

        # Check current report status before overwriting
        report_resp = table.get_item(
            Key={'PK': f'REPORT#{report_ticket}', 'SK': 'META'}
        )
        report = report_resp.get('Item')
        if not report:
            print(f"  WARN: Report {report_ticket} not found (task {task.get('task_id')})")
            skipped += 1
            continue

        current_report_status = report.get('status', 'pending')
        if current_report_status == status:
            skipped += 1
            continue

        # Update
        ts = now()
        table.update_item(
            Key={'PK': f'REPORT#{report_ticket}', 'SK': 'META'},
            UpdateExpression='SET #st = :s, updated_at = :t, GSI1PK = :gsi',
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':s': status,
                ':t': ts,
                ':gsi': f'STATUS#{status}',
            },
        )
        print(f"  UPDATED {report_ticket}: {current_report_status} → {status}")
        updated += 1

    print(f"\nDone. Updated: {updated}  |  Skipped: {skipped}")


if __name__ == '__main__':
    main()
