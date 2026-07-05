# procurement_engine.py
# Executes procurement actions after owner approval
# Generates POs, updates inventory, notifies supplier

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
    Creates a unique Purchase Order number.
    Format: SUTRA-YYYYMMDD-HHMMSS
    Example: SUTRA-20260711-113401
    """
    now = datetime.now()
    return f"SUTRA-{now.strftime('%Y%m%d-%H%M%S')}"


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
    Adds ordered quantity to current weight as
    'expected incoming stock'.
    """
    db = SessionLocal()
    try:
        inventory = db.query(Inventory).filter(
            Inventory.item_name == item_name
        ).first()

        if inventory:
            # Add expected stock to current weight
            inventory.current_weight += quantity_ordered
            inventory.last_updated = datetime.now()
            db.commit()
            print(f"[ENGINE] Inventory updated: {item_name} now {inventory.current_weight}kg expected")

    finally:
        db.close()


# ─── SAVE ORDER TO DATABASE ───────────────────────────────────

def save_order_to_db(order_data: dict):
    """
    Saves the procurement order to SQLite database.
    Returns the saved order object.
    """
    db = SessionLocal()
    try:
        order = ProcurementOrder(
            po_number=order_data["po_number"],
            item=order_data["item"],
            quantity=order_data["quantity"],
            supplier=order_data["supplier"],
            unit_price=order_data["unit_price"],
            total_cost=order_data["total_cost"],
            savings=order_data["savings"],
            status="approved",
            reasoning=order_data["reasoning"],
            expected_delivery=order_data["expected_delivery"]
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        print(f"[ENGINE] Order saved to database: {order_data['po_number']}")
        return order

    finally:
        db.close()


# ─── UPDATE ORDER STATUS ──────────────────────────────────────

def update_order_status(po_number: str, new_status: str):
    """
    Updates the status of an existing order.
    Status flow:
    pending_approval → approved → confirmed → delivered
    pending_approval → rejected
    """
    db = SessionLocal()
    try:
        order = db.query(ProcurementOrder).filter(
            ProcurementOrder.po_number == po_number
        ).first()

        if order:
            order.status = new_status
            db.commit()
            print(f"[ENGINE] Order {po_number} status: {new_status}")
            return True
        return False

    finally:
        db.close()


# ─── GET ORDER BY PO NUMBER ───────────────────────────────────

def get_order(po_number: str):
    """
    Fetches a specific order from database.
    Used when supplier confirms or rejects.
    """
    db = SessionLocal()
    try:
        order = db.query(ProcurementOrder).filter(
            ProcurementOrder.po_number == po_number
        ).first()
        return order
    finally:
        db.close()


# ─── MAIN FUNCTION: EXECUTE PROCUREMENT ───────────────────────

async def execute_procurement(recommendation: dict):
    """
    Main function called when owner approves.
    Orchestrates entire procurement execution.
    """
    print(f"\n[ENGINE] Executing procurement for {recommendation['item']}")

    # Step 1: Generate unique PO number
    po_number = generate_po_number()
    print(f"[ENGINE] Generated PO: {po_number}")

    # Step 2: Calculate delivery date
    delivery_date = calculate_delivery_date(
        recommendation["expected_delivery_days"]
    )

    # Step 3: Build complete order data
    order_data = {
        "po_number": po_number,
        "item": recommendation["item"],
        "quantity": recommendation["quantity"],
        "supplier": recommendation["supplier"],
        "unit_price": recommendation["unit_price"],
        "total_cost": recommendation["total_cost"],
        "savings": recommendation["savings"],
        "reasoning": recommendation["reasoning"],
        "expected_delivery": delivery_date
    }

    # Step 4: Save to database
    save_order_to_db(order_data)

    # Step 5: Update inventory forecast
    update_inventory_forecast(
        recommendation["item"],
        recommendation["quantity"]
    )

    # Step 6: Notify supplier portal via WebSocket
    if broadcast_to_supplier:
        await broadcast_to_supplier(order_data)
        print(f"[ENGINE] Supplier portal notified")

    # Step 7: Notify owner dashboard
    if broadcast_to_owner:
        await broadcast_to_owner({
            "type": "procurement_executed",
            "po_number": po_number,
            "item": recommendation["item"],
            "supplier": recommendation["supplier"],
            "quantity": recommendation["quantity"],
            "expected_delivery": delivery_date,
            "timestamp": datetime.now().isoformat()
        })

    print(f"[ENGINE] Procurement complete: {po_number}")
    return order_data


# ─── HANDLE OWNER REJECTION ───────────────────────────────────

def handle_rejection(po_number: str, reason: str = "Owner rejected"):
    """
    Called when owner taps Reject on mobile.
    Updates order status and logs reason.
    """
    update_order_status(po_number, "rejected")
    print(f"[ENGINE] Order {po_number} rejected: {reason}")


# ─── GET ANALYTICS SUMMARY ────────────────────────────────────

def get_analytics_summary():
    """
    Returns business summary for dashboard.
    Total savings, orders placed, best supplier etc.
    """
    db = SessionLocal()
    try:
        all_orders = db.query(ProcurementOrder).all()

        if not all_orders:
            return {
                "total_orders": 0,
                "total_savings": 0,
                "best_supplier": "N/A",
                "confirmed_orders": 0
            }

        total_savings = sum(o.savings for o in all_orders if o.savings)
        confirmed = [o for o in all_orders if o.status == "confirmed"]

        # Find most used supplier
        supplier_counts = {}
        for order in all_orders:
            supplier_counts[order.supplier] = \
                supplier_counts.get(order.supplier, 0) + 1
        best_supplier = max(supplier_counts, key=supplier_counts.get)

        return {
            "total_orders": len(all_orders),
            "total_savings": round(total_savings, 2),
            "best_supplier": best_supplier,
            "confirmed_orders": len(confirmed)
        }

    finally:
        db.close()