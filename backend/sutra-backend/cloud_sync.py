# cloud_sync.py
# Syncs completed transactions to Qualcomm AI Cloud 100
# Demo mode keeps cloud disabled.

import time
import threading
import httpx
from datetime import datetime
from config import USE_REAL_CLOUD, CLOUD_100_URL, CLOUD_100_API_KEY

STORE_ID = "SUTRA-STORE-001"
STORE_REGION = "south_india"

sync_queue = []

cloud_insights = {
    "regional_demand_trends": {},
    "supplier_performance": {},
    "seasonal_patterns": {},
    "last_updated": None
}


def is_connected():
    try:
        httpx.get("http://8.8.8.8", timeout=3)
        return True
    except Exception:
        return False


def anonymize_transaction_dict(order_data: dict):
    category_map = {
        "Rice": "grain",
        "Sugar": "sweetener",
        "Oil": "cooking_oil"
    }

    return {
        "item_category": category_map.get(order_data.get("item"), "general"),
        "event_type": "consumption_spike",
        "quantity_ordered": order_data.get("quantity", 0),
        "supplier_tier": "local_tier_1",
        "savings_achieved": order_data.get("savings", 0),
        "timestamp": datetime.now().isoformat(),
        "region": STORE_REGION
    }


def queue_transaction(order_data: dict):
    """
    Adds a completed transaction to the sync queue.
    Demo mode skips queueing so cloud stays out of the live flow.
    """
    if not USE_REAL_CLOUD:
        print("[CLOUD] Demo mode: cloud sync disabled; skipping queue.")
        return

    sync_queue.append({
        "data": order_data,
        "queued_at": datetime.now().isoformat(),
        "attempts": 0
    })
    print(f"[CLOUD] Transaction queued. Queue size: {len(sync_queue)}")


def mock_cloud_sync(transactions):
    print(f"[CLOUD MOCK] Syncing {len(transactions)} transactions")
    time.sleep(1)
    return {
        "status": "success",
        "processed": len(transactions),
        "insights": {
            "regional_demand_trends": {
                "Rice": {"trend": "increasing", "factor": 1.28},
                "Sugar": {"trend": "stable", "factor": 1.0},
                "Oil": {"trend": "slightly_increasing", "factor": 1.1}
            },
            "supplier_performance": {
                "local_tier_1": {"avg_reliability": 95.5},
                "local_tier_2": {"avg_reliability": 78.0}
            },
            "seasonal_patterns": {
                "festival_demand_multiplier": 1.3,
                "monsoon_demand_shift": 0.9
            }
        }
    }


def real_cloud_sync(transactions):
    payload = {
        "store_id": STORE_ID,
        "region": STORE_REGION,
        "transactions": transactions,
        "timestamp": datetime.now().isoformat()
    }

    headers = {
        "Authorization": f"Bearer {CLOUD_100_API_KEY}",
        "Content-Type": "application/json"
    }

    response = httpx.post(
        f"{CLOUD_100_URL}/sync",
        json=payload,
        headers=headers,
        timeout=30
    )

    return response.json()


def process_sync_queue():
    global cloud_insights

    if not sync_queue:
        return

    print(f"[CLOUD] Processing {len(sync_queue)} queued transactions")

    transactions = [
        anonymize_transaction_dict(item["data"])
        for item in sync_queue
    ]

    try:
        if USE_REAL_CLOUD:
            response = real_cloud_sync(transactions)
        else:
            response = mock_cloud_sync(transactions)

        if response.get("status") == "success":
            if "insights" in response:
                cloud_insights.update(response["insights"])
                cloud_insights["last_updated"] = datetime.now().isoformat()
                print(f"[CLOUD] Insights updated from Cloud 100")

            sync_queue.clear()
            print(f"[CLOUD] Sync complete. Queue cleared.")
        else:
            print(f"[CLOUD] Sync failed: {response}")

    except Exception as e:
        print(f"[CLOUD] Sync error: {e}")


def sync_worker():
    print("[CLOUD] Background sync worker started")

    while True:
        time.sleep(60)

        if sync_queue:
            print(f"[CLOUD] Checking connectivity... Queue: {len(sync_queue)}")

            if is_connected():
                print("[CLOUD] Connected! Syncing...")
                process_sync_queue()
            else:
                print("[CLOUD] No internet. Will retry in 60 seconds.")
        else:
            print("[CLOUD] Queue empty. Nothing to sync.")


def get_insights():
    return cloud_insights


def start_cloud_sync():
    """
    Starts the background sync thread.
    Demo mode disables cloud entirely.
    """
    if not USE_REAL_CLOUD:
        print("[CLOUD] Demo mode: cloud sync service disabled.")
        return None

    thread = threading.Thread(target=sync_worker, daemon=True)
    thread.start()
    print("[CLOUD] Cloud sync service started")
    return thread
