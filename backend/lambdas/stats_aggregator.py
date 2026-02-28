"""
SanitiSense AI — Stats Aggregator Lambda (DynamoDB Streams)
Triggered by DynamoDB Streams — NOT by API Gateway.

Why this exists (plain English):
  The naive approach in dashboard_api.py is to scan the entire reports table and
  count everything. When you have 100 reports, that's fine. When you have
  1,000,000 reports, that's:
    - Slow (takes seconds)
    - Expensive (DynamoDB charges per item read)
    - Unreliable under load

  The solution: every time a report is ADDED or UPDATED in the main table, this
  tiny Lambda fires and does ONE thing — it updates a running counter in a
  separate "AggregatedStats" table.

  So the dashboard_api.py can always read stats in O(1) with a single GetItem,
  no matter how many millions of reports exist.

AggregatedStats table structure:
  pk = "GLOBAL"    ← one row to rule them all
  sk = "STATS"
  total_reports    ← total ever
  pending_count
  in_progress_count
  completed_count
  spam_count
  category_garbage_pile
  category_overflowing_drain
  ... (one counter per category)
"""

import json
import os

import boto3

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
stats_table = dynamodb.Table(os.environ.get('STATS_TABLE', 'sanitisense-stats'))

# Valid report statuses — used to build counter attribute names
VALID_STATUSES = ['pending', 'in_progress', 'completed', 'spam', 'pending_ai',
                  'assigned', 'verified', 'rejected']

# Valid categories — used to build counter attribute names
VALID_CATEGORIES = ['garbage_pile', 'overflowing_drain', 'blocked_sewer',
                    'stagnant_water', 'medical_waste', 'animal_carcass', 'other']


def _status_key(status: str) -> str:
    """Convert a status name to a DynamoDB attribute name. e.g. 'in_progress' → 'count_in_progress'"""
    return f"count_{status}" if status in VALID_STATUSES else "count_other"


def _category_key(category: str) -> str:
    """Convert a category name to a DynamoDB attribute name. e.g. 'garbage_pile' → 'cat_garbage_pile'"""
    return f"cat_{category}" if category in VALID_CATEGORIES else "cat_other"


def _is_report(record_keys: dict) -> bool:
    """Check if the DynamoDB record is a REPORT (not a TASK or other item type)."""
    pk = record_keys.get('pk', {}).get('S', '')
    sk = record_keys.get('sk', {}).get('S', '')
    return pk.startswith('REPORT#') and sk == 'METADATA'


def build_update_expression(increments: dict) -> tuple:
    """
    Build a DynamoDB update expression that atomically increments/decrements
    multiple counters at once.

    Example increments: {'total_reports': 1, 'count_pending': 1, 'cat_garbage_pile': 1}
    Returns: (UpdateExpression, ExpressionAttributeNames, ExpressionAttributeValues)
    """
    set_parts = []
    names = {}
    values = {}

    for i, (attr, delta) in enumerate(increments.items()):
        name_placeholder = f'#a{i}'
        value_placeholder = f':v{i}'
        zero_placeholder = f':z{i}'

        # ADD is safe for counters — if the attribute doesn't exist yet, it starts from 0
        set_parts.append(
            f'{name_placeholder} = if_not_exists({name_placeholder}, {zero_placeholder}) + {value_placeholder}'
        )
        names[name_placeholder] = attr
        values[value_placeholder] = delta
        values[zero_placeholder] = 0

    return (
        'SET ' + ', '.join(set_parts),
        names,
        values,
    )


def handler(event, context):
    """
    DynamoDB Streams handler.
    Each event contains one or more change records from the main table.
    We only care about REPORT#... items.

    Stream event types:
      INSERT — new report was added
      MODIFY — existing report was updated (e.g. status changed)
      REMOVE — report was deleted (rare)

    Always returns {'batchItemFailures': [...]} so the stream knows the result.
    """
    batch_item_failures = []

    for record in event.get('Records', []):
        event_name = record['eventName']  # INSERT | MODIFY | REMOVE
        keys = record['dynamodb'].get('Keys', {})

        # Skip non-report items (tasks, worker records, etc.) — not an error
        if not _is_report(keys):
            continue

        new_image = record['dynamodb'].get('NewImage', {})
        old_image = record['dynamodb'].get('OldImage', {})

        increments = {}

        if event_name == 'INSERT':
            new_status = new_image.get('status', {}).get('S', 'pending')
            new_category = new_image.get('category', {}).get('S', 'other')
            increments['total_reports'] = 1
            increments[_status_key(new_status)] = 1
            increments[_category_key(new_category)] = 1

        elif event_name == 'MODIFY':
            old_status = old_image.get('status', {}).get('S', '')
            new_status = new_image.get('status', {}).get('S', '')
            if old_status != new_status:
                if old_status:
                    increments[_status_key(old_status)] = -1
                if new_status:
                    increments[_status_key(new_status)] = 1

        elif event_name == 'REMOVE':
            old_status = old_image.get('status', {}).get('S', '')
            old_category = old_image.get('category', {}).get('S', 'other')
            increments['total_reports'] = -1
            if old_status:
                increments[_status_key(old_status)] = -1
            increments[_category_key(old_category)] = -1

        if not increments:
            continue

        expr, names, values = build_update_expression(increments)
        try:
            stats_table.update_item(
                Key={'pk': 'GLOBAL', 'sk': 'STATS'},
                UpdateExpression=expr,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
            )
            print(f"[stats_aggregator] {event_name} → updated counters: {increments}")
        except Exception as e:
            print(f"[stats_aggregator] ERROR updating stats: {e}")
            # Re-raise so the stream retries this batch
            raise

    # Always return this — empty list means all records succeeded
    return {'batchItemFailures': batch_item_failures}


# ─── Local testing ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Testing helper functions...")

    assert _status_key('pending') == 'count_pending'
    assert _status_key('in_progress') == 'count_in_progress'
    assert _status_key('unknown_xyz') == 'count_other'
    print("  _status_key() ✓")

    assert _category_key('garbage_pile') == 'cat_garbage_pile'
    assert _category_key('random') == 'cat_other'
    print("  _category_key() ✓")

    expr, names, values = build_update_expression({'total_reports': 1, 'count_pending': 1})
    assert 'SET' in expr
    assert len(names) == 2
    print(f"  build_update_expression() ✓  → {expr}")

    print("\nAll local tests passed.")
    print("Note: handler() requires DynamoDB. Run tests/test_lambdas.py for full moto testing.")
