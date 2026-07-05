# agent_bridge.py
# Connects Arduino events to Phi-3 AI reasoning pipeline
# Before July 11: uses mock AI response
# After July 11: calls real Phi-3 Mini on Snapdragon NPU

import json
from datetime import datetime, timedelta
from config import USE_REAL_AI, SALES_HISTORY_DAYS
from database import SessionLocal, Inventory, Supplier, SalesHistory

# This will be set by main.py
# Points to websocket_manager's broadcast function
on_recommendation_ready = None


# ─── MOCK AI RESPONSE ─────────────────────────────────────────
# Simulates what Phi-3 Mini would return
# Replace with real inference on July 11

def mock_phi3_inference(context):
    """
    Simulates Phi-3 Mini reasoning.
    Takes business context, returns procurement recommendation.
    """
    item = context["item"]
    suppliers = context["suppliers"]

    # Pick the supplier with highest reliability
    best_supplier = max(suppliers, key=lambda s: s["reliability_score"])

    # Calculate alternative supplier cost for savings
    other_suppliers = [s for s in suppliers if s != best_supplier]
    if other_suppliers:
        worst = max(other_suppliers, key=lambda s: s["price_per_unit"])
        savings = (worst["price_per_unit"] - best_supplier["price_per_unit"]) * 30
    else:
        savings = 0

    return {
        "recommendation": f"Order 30kg {item}",
        "supplier": best_supplier["supplier_name"],
        "quantity": 30,
        "unit_price": best_supplier["price_per_unit"],
        "total_cost": best_supplier["price_per_unit"] * 30,
        "savings": round(savings, 2),
        "reasoning": f"Demand increased recently. {best_supplier['supplier_name']} has {best_supplier['reliability_score']}% reliability and lowest price.",
        "confidence": 94,
        "expected_delivery_days": best_supplier["lead_time_days"]
    }


# ─── REAL PHI-3 INFERENCE ─────────────────────────────────────
# Uncomment and use on July 11 with Qualcomm AI Hub

def real_phi3_inference(context):
    """
    Calls actual Phi-3 Mini on Snapdragon NPU via Qualcomm AI Hub.
    Member 2 will provide the exact implementation.
    """
    # Import Member 2's inference module
    # This path will be confirmed with Member 2
    import sys
    sys.path.append("../../ml")
    from agent import run_inference

    result = run_inference(context)
    return result


# ─── FETCH BUSINESS CONTEXT ───────────────────────────────────

def get_business_context(item_name):
    """
    Fetches all relevant business data for the item.
    This is what gets sent to Phi-3 for reasoning.
    """
    db = SessionLocal()

    try:
        # Get current inventory level
        inventory = db.query(Inventory).filter(
            Inventory.item_name == item_name
        ).first()

        # Get all suppliers for this item
        suppliers = db.query(Supplier).filter(
            Supplier.item == item_name
        ).all()

        # Get sales history for last N days
        cutoff_date = (datetime.now() - timedelta(
            days=SALES_HISTORY_DAYS)
        ).strftime("%Y-%m-%d")

        sales = db.query(SalesHistory).filter(
            SalesHistory.item == item_name,
            SalesHistory.date >= cutoff_date
        ).all()

        # Calculate average daily sales
        if sales:
            avg_daily_sales = sum(s.quantity_sold for s in sales) / len(sales)
        else:
            avg_daily_sales = 0

        # Package everything into context dict
        context = {
            "item": item_name,
            "remaining_weight": inventory.current_weight if inventory else 0,
            "reorder_threshold": inventory.reorder_threshold if inventory else 5,
            "unit": inventory.unit if inventory else "kg",
            "avg_daily_sales": round(avg_daily_sales, 2),
            "sales_trend": [s.quantity_sold for s in sales[-7:]],
            "suppliers": [
                {
                    "supplier_name": s.supplier_name,
                    "price_per_unit": s.price_per_unit,
                    "reliability_score": s.reliability_score,
                    "lead_time_days": s.lead_time_days
                }
                for s in suppliers
            ],
            "upcoming_festivals": check_upcoming_festivals(),
            "timestamp": datetime.now().isoformat()
        }

        return context

    finally:
        db.close()


# ─── FESTIVAL CALENDAR ────────────────────────────────────────

def check_upcoming_festivals():
    """
    Returns list of festivals in next 7 days.
    In real version this would check a proper calendar.
    For demo we hardcode a festival near July 11-12.
    """
    festivals = []
    today = datetime.now()

    # Hardcoded for demo — festival on July 12
    demo_festival_date = datetime(2026, 7, 12)
    days_until = (demo_festival_date - today).days

    if 0 <= days_until <= 7:
        festivals.append({
            "name": "Local Festival",
            "days_away": days_until
        })

    return festivals


# ─── MAIN HANDLER: PROCESS ARDUINO EVENT ──────────────────────

def handle_arduino_event(event):
    """
    Main function called by serial_listener when event arrives.
    Orchestrates: context fetch → AI inference → forward result
    """
    print(f"\n[AGENT] Event received: {event['event']} for {event['item']}")

    # Only process actionable events
    if event["event"] == "normal":
        print("[AGENT] Normal consumption — no action needed")
        return

    item_name = event["item"]

    # Step 1: Fetch business context from database
    print(f"[AGENT] Fetching business context for {item_name}...")
    context = get_business_context(item_name)
    print(f"[AGENT] Context ready: {len(context['suppliers'])} suppliers found")

    # Step 2: Run AI inference
    print("[AGENT] Running AI inference...")
    if USE_REAL_AI:
        recommendation = real_phi3_inference(context)
    else:
        recommendation = mock_phi3_inference(context)

    print(f"[AGENT] Recommendation: {recommendation['recommendation']}")

    # Step 3: Package result with original event
    result = {
        "event": event,
        "context": context,
        "recommendation": recommendation,
        "status": "pending_approval",
        "timestamp": datetime.now().isoformat()
    }

    # Step 4: Send to websocket_manager to push to frontends
    if on_recommendation_ready:
        on_recommendation_ready(result)

    return result