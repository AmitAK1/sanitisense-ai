"""
SanitiSense AI — Seed Worker Profiles
Run this script once to add 5 demo worker records to DynamoDB.

Usage:
    cd infrastructure
    python seed_workers.py

Workers will be seeded as:
  PK = WORKER#W-001   SK = PROFILE
  PK = WORKER#W-002   SK = PROFILE
  ... etc.

These match the hardcoded workers referenced in the demo.
"""

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SanitiSense')

WORKERS = [
    {
        'PK': 'WORKER#W-001',
        'SK': 'PROFILE',
        'worker_id': 'W-001',
        'name': 'Ramesh Kumar',
        'ward_assigned': 7,       # Andheri East
        'status': 'active',
        'phone': '9876543210',
        'total_completed': 45,
        'avg_rating': 4.3,
        'created_at': '2026-01-01T00:00:00Z',
    },
    {
        'PK': 'WORKER#W-002',
        'SK': 'PROFILE',
        'worker_id': 'W-002',
        'name': 'Priya Nair',
        'ward_assigned': 3,       # Byculla
        'status': 'active',
        'phone': '9123456780',
        'total_completed': 38,
        'avg_rating': 4.6,
        'created_at': '2026-01-01T00:00:00Z',
    },
    {
        'PK': 'WORKER#W-003',
        'SK': 'PROFILE',
        'worker_id': 'W-003',
        'name': 'Ajay Sharma',
        'ward_assigned': 10,      # Kurla
        'status': 'active',
        'phone': '9988776655',
        'total_completed': 62,
        'avg_rating': 4.1,
        'created_at': '2026-01-01T00:00:00Z',
    },
    {
        'PK': 'WORKER#W-004',
        'SK': 'PROFILE',
        'worker_id': 'W-004',
        'name': 'Meena Patil',
        'ward_assigned': 5,       # Dadar
        'status': 'active',
        'phone': '8877665544',
        'total_completed': 29,
        'avg_rating': 4.5,
        'created_at': '2026-01-01T00:00:00Z',
    },
    {
        'PK': 'WORKER#W-005',
        'SK': 'PROFILE',
        'worker_id': 'W-005',
        'name': 'Suresh Desai',
        'ward_assigned': 12,      # Borivali
        'status': 'active',
        'phone': '7766554433',
        'total_completed': 51,
        'avg_rating': 4.2,
        'created_at': '2026-01-01T00:00:00Z',
    },
]


def seed_workers():
    print("Seeding worker profiles into DynamoDB...")
    with table.batch_writer() as batch:
        for worker in WORKERS:
            batch.put_item(Item=worker)
    print(f"✓ Seeded {len(WORKERS)} worker profiles:")
    for w in WORKERS:
        print(f"  {w['worker_id']} — {w['name']} (Ward {w['ward_assigned']})")


if __name__ == '__main__':
    seed_workers()
    print("\nDone! Workers are now accessible via GET /worker/{id}/profile")
    print("Example: GET /worker/W-001/profile")
