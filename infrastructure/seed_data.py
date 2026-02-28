"""
SanitiSense AI — Seed Data Script
Populates DynamoDB with 50+ demo reports for the hackathon demo.

Usage:
  pip install boto3
  python seed_data.py

Make sure AWS credentials are configured and the DynamoDB table exists.
"""

import json
import random
import uuid
from datetime import datetime, timedelta

# TODO: uncomment when deploying
# import boto3
# dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
# table = dynamodb.Table('SanitiSense')

# ========== DEMO DATA CONFIGURATION ==========
MUMBAI_WARDS = [
    {"number": 1, "name": "Colaba", "lat": 18.9067, "lng": 72.8147},
    {"number": 3, "name": "Byculla", "lat": 18.9784, "lng": 72.8318},
    {"number": 5, "name": "Dadar", "lat": 19.0178, "lng": 72.8478},
    {"number": 7, "name": "Andheri East", "lat": 19.1136, "lng": 72.8697},
    {"number": 10, "name": "Kurla", "lat": 19.0726, "lng": 72.8794},
    {"number": 12, "name": "Borivali", "lat": 19.2288, "lng": 72.8544},
    {"number": 15, "name": "Thane Road", "lat": 19.1834, "lng": 72.9517},
    {"number": 18, "name": "Malad", "lat": 19.1874, "lng": 72.8484},
    {"number": 22, "name": "Jogeshwari", "lat": 19.1364, "lng": 72.8496},
    {"number": 24, "name": "Goregaon", "lat": 19.1663, "lng": 72.8526},
]

CATEGORIES = [
    ("garbage_pile", "Large garbage accumulation", 0.30),
    ("overflowing_drain", "Drain overflowing onto the road", 0.22),
    ("blocked_sewer", "Sewer blockage causing water backup", 0.18),
    ("stagnant_water", "Stagnant water pooling in area", 0.15),
    ("medical_waste", "Medical waste found in open area", 0.08),
    ("animal_carcass", "Animal carcass on the road", 0.04),
    ("other", "Other sanitation issue", 0.03),
]

DESCRIPTIONS = {
    "garbage_pile": [
        "Large pile of mixed waste near apartment entrance, causing foul smell",
        "Garbage accumulated for 3+ days, plastic bags scattered across the road",
        "Overflowing garbage bin near school, organic waste visible",
        "Construction debris mixed with household garbage near park",
        "Garbage dump site overflowing, dogs tearing through waste bags",
    ],
    "overflowing_drain": [
        "Drain overflowing with grey water near residential complex",
        "Storm drain clogged, water flowing onto pedestrian walkway",
        "Open drain overflowing, sewage water reaching shop entrances",
        "Drain water mixed with garbage creating road blockage",
    ],
    "blocked_sewer": [
        "Main sewer line blocked, backup visible through manhole",
        "Sewer blockage causing road flooding near bus stop",
        "Sewer pipe burst, contaminated water on the street",
    ],
    "stagnant_water": [
        "Large pool of stagnant water near children's playground",
        "Stagnant water in construction site pit, mosquito larvae visible",
        "Waterlogged area after drain blockage, standing for 4+ days",
        "Stagnant water near vegetable market, contamination risk high",
    ],
    "medical_waste": [
        "Used syringes and bandages found in public garbage bin",
        "Medical waste bags dumped near residential area",
    ],
    "animal_carcass": [
        "Dead dog carcass on main road, not removed for 2 days",
        "Dead rat cluster near food stall area",
    ],
    "other": [
        "Broken public toilet, sewage leaking",
        "Illegal dumping of chemical waste near stream",
    ],
}

STATUSES = ["pending", "assigned", "in_progress", "completed", "verified"]


def generate_report(index):
    """Generate a single demo report"""
    # Random category weighted by frequency
    categories, descriptions, weights = zip(*CATEGORIES)
    category = random.choices(categories, weights=weights, k=1)[0]
    
    # Random ward
    ward = random.choice(MUMBAI_WARDS)
    
    # Random time in last 7 days
    hours_ago = random.randint(1, 168)  # 1-168 hours = 7 days
    created_at = datetime(2026, 2, 28) - timedelta(hours=hours_ago)
    
    # Random severity (weighted toward medium-high for realistic data)
    severity = random.choices(range(1, 11), weights=[1, 2, 3, 5, 7, 8, 9, 7, 4, 2], k=1)[0]
    
    # Status weighted toward completed for demo
    if hours_ago > 48:
        status = random.choices(STATUSES, weights=[5, 5, 10, 50, 30], k=1)[0]
    elif hours_ago > 12:
        status = random.choices(STATUSES, weights=[10, 15, 40, 25, 10], k=1)[0]
    else:
        status = random.choices(STATUSES, weights=[40, 30, 20, 8, 2], k=1)[0]
    
    report_id = f"RPT-{created_at.strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    task_id = f"TSK-{created_at.strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    # Slight location randomization within ward
    lat = ward["lat"] + random.uniform(-0.005, 0.005)
    lng = ward["lng"] + random.uniform(-0.005, 0.005)
    
    description = random.choice(DESCRIPTIONS.get(category, ["Sanitation issue reported"]))
    
    health_risk = "high" if severity >= 8 else "medium" if severity >= 5 else "low"
    
    report = {
        "PK": f"REPORT#{report_id}",
        "SK": "META",
        "report_id": report_id,
        "task_id": task_id,
        "category": category,
        "severity_score": severity,
        "description": description,
        "health_risk": health_risk,
        "status": status,
        "ward_number": ward["number"],
        "ward_name": ward["name"],
        "location": {"lat": round(lat, 6), "lng": round(lng, 6)},
        "image_key": f"citizen-reports/2026/02/{created_at.strftime('%d')}/{report_id}.jpg",
        "created_at": created_at.isoformat() + "Z",
        "updated_at": (created_at + timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
        "citizen_phone": f"+91-{random.randint(7000000000, 9999999999)}",
        "ai_confidence": round(random.uniform(0.75, 0.98), 2),
        # GSI keys
        "GSI1PK": f"STATUS#{status}",
        "GSI1SK": created_at.isoformat() + "Z"
    }
    
    return report


def generate_all_seed_data():
    """Generate 50 demo reports"""
    reports = [generate_report(i) for i in range(50)]
    return reports


def upload_to_dynamodb(reports):
    """Batch write to DynamoDB"""
    # TODO: uncomment when deploying
    # with table.batch_writer() as batch:
    #     for report in reports:
    #         batch.put_item(Item=report)
    # print(f"Uploaded {len(reports)} reports to DynamoDB")
    pass


if __name__ == "__main__":
    print("Generating 50 demo reports...")
    reports = generate_all_seed_data()
    
    # Print summary
    status_counts = {}
    category_counts = {}
    for r in reports:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
        category_counts[r["category"]] = category_counts.get(r["category"], 0) + 1
    
    print(f"\n=== Seed Data Summary ===")
    print(f"Total reports: {len(reports)}")
    print(f"\nBy Status:")
    for s, c in sorted(status_counts.items()):
        print(f"  {s}: {c}")
    print(f"\nBy Category:")
    for cat, c in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {c}")
    
    # Save to JSON for reference
    with open("seed_data_output.json", "w") as f:
        json.dump(reports, f, indent=2, default=str)
    print(f"\nSaved to seed_data_output.json")
    
    # Upload to DynamoDB
    # TODO: uncomment when ready to deploy
    # upload_to_dynamodb(reports)
    # print("Uploaded to DynamoDB!")
