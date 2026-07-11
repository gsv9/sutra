# cloud_sync.py
# Syncs completed transactions to Qualcomm AI Cloud 100
# Queues locally when offline, syncs when internet available
# Keeps business data private — only anonymized patterns sent

import json
import time
import threading
import httpx
from datetime import datetime
from database import SessionLocal, ProcurementOrder
from config import USE_REAL_CLOUD, CLOUD_100_URL, CLOUD_100_API_KEY

# Store ID for this deployment
# Each store gets a unique ID — no personal info
STORE_ID = "SUTRA-STORE-001"
STORE_REGION = "south_india"

# Local queue for transactions waiting to sync
# When offline, transactions pile up here
sync_queue = []

# Last insights received from Cloud 100
# Used by agent_bridge to improve recommendations
cloud_insights = {
    "regional_demand_trends": {},
    "supplier_performance": {},
    "seasonal_patterns": {},
    "last_updated": None
}


# ─── CHECK INTERNET CONNECTIVITY ──────────────────────────────

def is_connected():
    """
    Checks if internet is available.
    Tries to reach Google DNS — fastest way to check.
    """
    try:
        httpx.get("http://8.8.8.8", timeout=3)
        return True
    except Exception:
        return False


# ─── ANONYMIZE TRANSACTION ────────────────────────────────────

def anonymize_transaction(order):
    """
    Removes all sensitive data before sending to cloud.
    Only keeps patterns — no names, no prices, no store info.
    """
    # Map supplier names to tiers (no actual names sent)
    supplier_tier = "local_tier_1"  # simplified for demo

    # Map item names to categories
    category_map = {
        "Rice": "grain",
        "Sugar": "sweetener",
        "Oil": "cooking_oil"
    }
    category = category_map.get(order.item, "general")

    return {
        "item_category": category,
        "event_type": "consumption_spike",
        "quantity_ordered": order.quantity,
        "supplier_tier": supplier_tier,
        "savings_achieved": order.savings or 0,
        "timestamp": str(order.created_at),
        "region": STORE_REGION
    }


# ─── ADD TO SYNC QUEUE ────────────────────────────────────────

def queue_transaction(order_data: dict):
    """
    Adds a completed transaction to the sync queue.
    Called by procurement_engine after order is confirmed.
    """
    sync_queue.append({
        "data": order_data,
        "queued_at": datetime.now().isoformat(),
        "attempts": 0
    })
    print(f"[CLOUD] Transaction queued. Queue size: {len(sync_queue)}")


# ─── MOCK CLOUD SYNC ──────────────────────────────────────────

def mock_cloud_sync(transactions):
    """
    Simulates Cloud 100 response for testing.
    Returns fake insights as if Cloud 100 responded.
    """
    print(f"[CLOUD MOCK] Syncing {len(transactions)} transactions")

    # Simulate cloud processing delay
    time.sleep(1)

    # Return mock insights
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


# ─── REAL CLOUD SYNC ──────────────────────────────────────────

def real_cloud_sync(transactions):
    """
    Sends transactions to actual Qualcomm AI Cloud 100.
    Fill in real endpoint on July 11 when credentials available.
    """
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


# ─── PROCESS SYNC QUEUE ───────────────────────────────────────

def process_sync_queue():
    """
    Attempts to sync all queued transactions to Cloud 100.
    Called by background thread when internet is detected.
    """
    global cloud_insights

    if not sync_queue:
        return

    print(f"[CLOUD] Processing {len(sync_queue)} queued transactions")

    # Anonymize all queued transactions
    transactions = [
        anonymize_transaction_dict(item["data"])
        for item in sync_queue
    ]

    try:
        # Use mock or real based on config
        if USE_REAL_CLOUD:
            response = real_cloud_sync(transactions)
        else:
            response = mock_cloud_sync(transactions)

        if response.get("status") == "success":
            # Update local insights from cloud response
            if "insights" in response:
                cloud_insights.update(response["insights"])
                cloud_insights["last_updated"] = datetime.now().isoformat()
                print(f"[CLOUD] Insights updated from Cloud 100")

            # Clear synced transactions from queue
            sync_queue.clear()
            print(f"[CLOUD] Sync complete. Queue cleared.")

        else:
            print(f"[CLOUD] Sync failed: {response}")

    except Exception as e:
        print(f"[CLOUD] Sync error: {e}")
        # Keep in queue — will retry next cycle


def anonymize_transaction_dict(order_data: dict):
    """
    Anonymizes a transaction dict (not a database object).
    Used when order comes in as dict from procurement_engine.
    """
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


# ─── BACKGROUND SYNC THREAD ───────────────────────────────────

def sync_worker():
    """
    Runs in background continuously.
    Every 60 seconds checks internet and syncs if available.
    """
    print("[CLOUD] Background sync worker started")

    while True:
        # Wait 60 seconds between sync attempts
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


# ─── GET CLOUD INSIGHTS ───────────────────────────────────────

def get_insights():
    """
    Returns latest insights from Cloud 100.
    Called by agent_bridge to improve recommendations.
    """
    return cloud_insights


# ─── START CLOUD SYNC SERVICE ─────────────────────────────────

def start_cloud_sync():
    """
    Starts the background sync thread.
    Called by main.py when server starts.
    """
    thread = threading.Thread(target=sync_worker, daemon=True)
    thread.start()
    print("[CLOUD] Cloud sync service started")
    return thread