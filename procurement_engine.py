# procurement_engine.py
# Executes procurement actions after owner approval/rejection
# Every stage (pending, approved, rejected) is saved as its own row —
# nothing is ever updated in place, full history is preserved.

from datetime import datetime, timedelta
from database import SessionLocal, Inventory, ProcurementOrder
import asyncio

# Points to websocket_manager broadcast functions
# Set by main.py when server starts
broadcast_to_supplier = None
broadcast_to_owner = None


# ─── GENERATE PO NUMBER ───────────────────────────────────────

def generate_po_number():
    """
    Creates a unique Purchase Order / recommendation number.
    Format: SUTRA-YYYYMMDD-HHMMSS-ffffff (microseconds added
    so rapid successive calls never collide).
    """
    now = datetime.now()
    return f"SUTRA-{now.strftime('%Y%m%d-%H%M%S-%f')}"


# ─── CALCULATE EXPECTED DELIVERY ──────────────────────────────

def calculate_delivery_date(lead_time_days: int):
    """
    Calculates expected delivery date based on
    supplier's lead time.
    """
    delivery_date = datetime.now() + timedelta(days=lead_time_days)
    return delivery_date.strftime("%Y-%m-%d %H:%M")


# ─── UPDATE INVENTORY AFTER ORDER ─────────────────────────────

def update_inventory_forecast(item_name: str, quantity_ordered: float):
    """
    Updates inventory to reflect incoming stock.
    """
    db = SessionLocal()
    try:
        inventory = db.query(Inventory).filter(
            Inventory.item_name == item_name
        ).first()

        if inventory:
            inventory.current_weight += quantity_ordered
            inventory.last_updated = datetime.now()
            db.commit()
            print(f"[ENGINE] Inventory updated: {item_name} now {inventory.current_weight}kg expected")

    finally:
        db.close()


# ─── SAVE RECOMMENDATION/ORDER AS A NEW ROW ───────────────────

def save_recommendation_to_db(po_number: str, item: str, recommendation: dict,
                               status: str, expected_delivery: str = ""):
    """
    Inserts a NEW row for a recommendation at any stage:
    pending_approval, approved, or rejected.

    This is never used to update an existing row — every
    stage of a recommendation's lifecycle gets its own
    permanent record.
    """
    db = SessionLocal()
    try:
        order = ProcurementOrder(
            po_number=po_number,
            item=item,
            quantity=recommendation["quantity"],
            supplier=recommendation["supplier"],
            unit_price=recommendation["unit_price"],
            total_cost=recommendation["total_cost"],
            savings=recommendation["savings"],
            status=status,
            reasoning=recommendation["reasoning"],
            expected_delivery=expected_delivery
        )
        db.add(order)
        db.commit()
        print(f"[ENGINE] {status} row saved: {po_number}")

    finally:
        db.close()


# ─── GET ORDER BY PO NUMBER ───────────────────────────────────

def get_order(po_number: str):
    """
    Fetches a specific order/recommendation row from database.
    """
    db = SessionLocal()
    try:
        order = db.query(ProcurementOrder).filter(
            ProcurementOrder.po_number == po_number
        ).first()
        return order
    finally:
        db.close()


# ─── MAIN FUNCTION: EXECUTE PROCUREMENT (APPROVAL) ────────────

async def execute_procurement(recommendation: dict):
    """
    Main function called when owner approves.
    Creates a NEW row with status='approved' — does not
    touch the original pending_approval row.

    `recommendation` must include the original po_number
    (from the pending recommendation), item, quantity,
    supplier, unit_price, total_cost, savings, reasoning,
    expected_delivery_days.
    """
    original_po = recommendation.get("po_number")
    print(f"\n[ENGINE] Executing procurement for {recommendation['item']} (from {original_po})")

    # New PO number for the approved record
    approved_po = generate_po_number()

    delivery_date = calculate_delivery_date(
        recommendation["expected_delivery_days"]
    )

    save_recommendation_to_db(
        po_number=approved_po,
        item=recommendation["item"],
        recommendation=recommendation,
        status="approved",
        expected_delivery=delivery_date
    )

    order_data = {
        "po_number": approved_po,
        "item": recommendation["item"],
        "quantity": recommendation["quantity"],
        "supplier": recommendation["supplier"],
        "unit_price": recommendation["unit_price"],
        "total_cost": recommendation["total_cost"],
        "savings": recommendation["savings"],
        "reasoning": recommendation["reasoning"],
        "expected_delivery": delivery_date
    }

    update_inventory_forecast(
        recommendation["item"],
        recommendation["quantity"]
    )

    if broadcast_to_supplier:
        await broadcast_to_supplier(order_data)
        print(f"[ENGINE] Supplier portal notified")

    if broadcast_to_owner:
        await broadcast_to_owner({
            "type": "procurement_executed",
            "po_number": approved_po,
            "item": recommendation["item"],
            "supplier": recommendation["supplier"],
            "quantity": recommendation["quantity"],
            "expected_delivery": delivery_date,
            "timestamp": datetime.now().isoformat()
        })

    from cloud_sync import queue_transaction
    queue_transaction(order_data)
    print(f"[ENGINE] Transaction queued for Cloud 100 sync")

    print(f"[ENGINE] Procurement complete: {approved_po}")
    return order_data


# ─── HANDLE OWNER REJECTION ───────────────────────────────────

def handle_rejection(recommendation: dict, reason: str = "Owner rejected"):
    """
    Called when owner taps Reject on mobile.
    Creates a NEW row with status='rejected'.

    `recommendation` must include item, quantity, supplier,
    unit_price, total_cost, savings, reasoning — the full
    recommendation object as broadcast to the frontend.
    """
    rejected_po = generate_po_number()

    save_recommendation_to_db(
        po_number=rejected_po,
        item=recommendation["item"],
        recommendation=recommendation,
        status="rejected"
    )

    print(f"[ENGINE] Rejected row saved: {rejected_po} — {reason}")
    return rejected_po


# ─── GET ANALYTICS SUMMARY ────────────────────────────────────

def get_analytics_summary():
    """
    Returns business summary for dashboard.
    Only counts APPROVED orders as real orders/savings —
    pending and rejected rows are excluded from these totals.
    """
    db = SessionLocal()
    try:
        approved_orders = db.query(ProcurementOrder).filter(
            ProcurementOrder.status == "approved"
        ).all()

        confirmed_orders = db.query(ProcurementOrder).filter(
            ProcurementOrder.status == "confirmed"
        ).all()

        if not approved_orders:
            return {
                "total_orders": 0,
                "total_savings": 0,
                "best_supplier": "N/A",
                "confirmed_orders": 0
            }

        total_savings = sum(o.savings for o in approved_orders if o.savings)

        supplier_counts = {}
        for order in approved_orders:
            supplier_counts[order.supplier] = \
                supplier_counts.get(order.supplier, 0) + 1
        best_supplier = max(supplier_counts, key=supplier_counts.get)

        return {
            "total_orders": len(approved_orders),
            "total_savings": round(total_savings, 2),
            "best_supplier": best_supplier,
            "confirmed_orders": len(confirmed_orders)
        }

    finally:
        db.close()