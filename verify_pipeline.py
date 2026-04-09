import asyncio
import json
import uuid
import time
import redis
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.app.models.database import Violation, Base

async def verify_redis_to_db():
    print("--- 🚀 Pipeline Verification Started ---")
    
    # 1. Connect to Redis (Sync for simple test)
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    try:
        r.ping()
        print("✅ Redis connection OK")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return

    # 2. Setup SQLite connection to check results
    db_url = "sqlite:///./data/safety.db"
    engine = create_engine(db_url)
    
    # 3. Create a unique violation event
    test_id = str(uuid.uuid4().hex)[:8]
    test_violation = {
        "camera_id": f"test_cam_{test_id}",
        "timestamp": time.time(),
        "event": {
            "violation_type": f"TEST_VIOLATION_{test_id}",
            "confidence": 0.99,
            "snapshot_path": "/tmp/test.jpg"
        }
    }
    
    print(f"📡 Publishing test violation: {test_violation['event']['violation_type']}...")
    r.publish("violations.raw", json.dumps(test_violation))
    
    # 4. Wait for worker to process
    print("⏳ Waiting 3 seconds for worker to process...")
    await asyncio.sleep(3)
    
    # 5. Check DB
    print("🔎 Checking Database for violation...")
    with Session(engine) as session:
        stmt = select(Violation).where(Violation.violation_type == test_violation['event']['violation_type'])
        result = session.execute(stmt).scalar_one_or_none()
        
        if result:
            print(f"✅ SUCCESS: Violation found in DB!")
            print(f"   - ID: {result.id}")
            print(f"   - Camera: {result.camera_id}")
            print(f"   - Timestamp: {result.timestamp}")
            print(f"   - Note: {result.notes}")
        else:
            print("❌ FAILURE: Violation NOT found in DB. Is the worker running?")

if __name__ == "__main__":
    asyncio.run(verify_redis_to_db())
