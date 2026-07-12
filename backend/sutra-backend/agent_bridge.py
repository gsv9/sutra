# agent_bridge.py
# Connects Arduino events to Phi-3 AI reasoning pipeline
# Before demo day: uses mock AI response
# On demo day: calls real Phi-3 Mini on Snapdragon NPU

import sys
from datetime import datetime, timedelta
from pathlib import Path

from config import USE_REAL_AI, SALES_HISTORY_DAYS, ML_PROJECT_ROOT
from database import SessionLocal, Inventory, Supplier, SalesHistory
from procurement_engine import save_recommendation_to_db, generate_po_number

# This will be set by main.py
# Points to websocket_manager's broadcast function
on_recommendation_ready = None


# ─── MOCK AI RESPONSE ───────────────────────────────────────────────────

def mock_phi3_inference(context):
    """
    Simulates Phi-3 Mini reasoning.
    Takes business context, returns procurement recommendation.
    """
    item = context["item"]
    suppliers = context["suppliers"]

    best_supplier = max(suppliers, key=lambda s: s["reliability_score"])

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
        "reasoning": (
            f"Demand increased recently. {best_supplier['supplier_name']} has "
            f"{best_supplier['reliability_score']}% reliability and lowest price."
        ),
        "confidence": 94,
        "expected_delivery_days": best_supplier["lead_time_days"]
    }


# ─── REAL PHI-3 INFERENCE ───────────────────────────────────────────────

def real_phi3_inference(context):
    """
    Calls the authoritative Phi-3 Mini inference pipeline.
    The backend points at the local integrated ML tree inside sutra_full.
    """
    ml_root = Path(ML_PROJECT_ROOT)

    if ml_root.exists():
        ml_root_str = str(ml_root)
        if ml_root_str not in sys.path:
            sys.path.insert(0, ml_root_str)

    try:
        from ml.agent import run_inference

        return run_inference(context)

    except Exception as exc:
        print(
            "[AGENT] Real ML backend unavailable "
            f"({exc}). Falling back to mock inference."
        )
        return mock_phi3_inference(context)


# ─── FETCH BUSINESS CONTEXT ─────────────────────────────────────────────

def get_business_context(item_name):
    """
    Fetches all relevant business data for the item.
    This is what gets sent to Phi-3 for reasoning.
    """
    db = SessionLocal()

    try:
        inventory = db.query(Inventory).filter(
            Inventory.item_name == item_name
        ).first()

        suppliers = db.query(Supplier).filter(
            Supplier.item == item_name
        ).all()

        cutoff_date = (datetime.now() - timedelta(
            days=SALES_HISTORY_DAYS)
        ).strftime("%Y-%m-%d")

        sales = db.query(SalesHistory).filter(
            SalesHistory.item == item_name,
            SalesHistory.date >= cutoff_date
        ).all()

        if sales:
            avg_daily_sales = sum(s.quantity_sold for s in sales) / len(sales)
        else:
            avg_daily_sales = 0

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


# ─── FESTIVAL CALENDAR ──────────────────────────────────────────────────

def check_upcoming_festivals():
    """
    Returns list of festivals in next 7 days.
    Hardcoded for demo — festival on July 12.
    """
    festivals = []
    today = datetime.now()

    demo_festival_date = datetime(2026, 7, 12)
    days_until = (demo_festival_date - today).days

    if 0 <= days_until <= 7:
        festivals.append({
            "name": "Local Festival",
            "days_away": days_until
        })

    return festivals


# ─── MAIN HANDLER: PROCESS ARDUINO EVENT ────────────────────────────────

def handle_arduino_event(event):
    """
    Main function called by serial_listener when event arrives.
    Orchestrates: context fetch → AI inference → save pending row → forward result
    """
    event_type = str(event.get("event", "NORMAL")).upper()
    item_name = event.get("item") or event.get("product") or "Rice"

    print(f"\n[AGENT] Event received: {event_type} for {item_name}")

    if event_type == "NORMAL":
        print("[AGENT] Normal consumption — no action needed")
        return

    print(f"[AGENT] Fetching business context for {item_name}...")
    context = get_business_context(item_name)
    print(f"[AGENT] Context ready: {len(context['suppliers'])} suppliers found")

    print("[AGENT] Running AI inference...")
    if USE_REAL_AI:
        recommendation = real_phi3_inference(context)
    else:
        recommendation = mock_phi3_inference(context)

    print(f"[AGENT] Recommendation: {recommendation['recommendation']}")

    po_number = generate_po_number()
    save_recommendation_to_db(
        po_number=po_number,
        item=item_name,
        recommendation=recommendation,
        status="pending_approval"
    )

    result = {
        "po_number": po_number,
        "event": event,
        "context": context,
        "recommendation": recommendation,
        "status": "pending_approval",
        "timestamp": datetime.now().isoformat()
    }

    return result
