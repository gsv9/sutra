from datetime import datetime, timedelta
from database import SessionLocal, Inventory, ProcurementOrder
import asyncio

broadcast_to_supplier = None
broadcast_to_owner = None

def generate_po_number():
    now = datetime.now()
    return f"SUTRA-{now.strftime('%Y%m%d-%H%M%S-%f')}"

def calculate_delivery_date(lead_time_days: int):
    delivery_date = datetime.now() + timedelta(days=lead_time_days)
    return delivery_date.strftime("%Y-%m-%d %H:%M")

def update_inventory_forecast(item_name: str, quantity_ordered: float):
    db = SessionLocal()
    try:
        inventory = db.query(Inventory).filter(Inventory.item_name == item_name).first()
        if inventory:
            inventory.current_weight += quantity_ordered
            inventory.last_updated = datetime.now()
            db.commit()
            print(f"[ENGINE] Inventory updated: {item_name} now {inventory.current_weight}kg expected")
    finally:
        db.close()

def save_recommendation_to_db(po_number: str, item: str, recommendation: dict, status: str, expected_delivery: str = ""):
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

def get_order(po_number: str):
    db = SessionLocal()
    try:
        order = db.query(ProcurementOrder).filter(ProcurementOrder.po_number == po_number).first()
        return order
    finally:
        db.close()

async def execute_procurement(recommendation: dict):
    original_po = recommendation.get("po_number")
    print(f"\n[ENGINE] Executing procurement for {recommendation['item']} (from {original_po})")

    approved_po = generate_po_number()
    delivery_date = calculate_delivery_date(recommendation["expected_delivery_days"])

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

    update_inventory_forecast(recommendation["item"], recommendation["quantity"])

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

def handle_rejection(recommendation: dict, reason: str = "Owner rejected"):
    rejected_po = generate_po_number()
    save_recommendation_to_db(
        po_number=rejected_po,
        item=recommendation["item"],
        recommendation=recommendation,
        status="rejected"
    )
    print(f"[ENGINE] Rejected row saved: {rejected_po} — {reason}")
    return rejected_po

def get_analytics_summary():
    db = SessionLocal()
    try:
        approved_orders = db.query(ProcurementOrder).filter(ProcurementOrder.status == "approved").all()
        confirmed_orders = db.query(ProcurementOrder).filter(ProcurementOrder.status == "confirmed").all()

        if not approved_orders:
            return {
                "total_orders": 0,
                "total_spent": 0,
                "best_supplier": "N/A",
                "confirmed_orders": 0
            }

        # REPLACED SAVINGS WITH TOTAL SPENT
        total_spent = sum(o.total_cost for o in approved_orders if o.total_cost)

        supplier_counts = {}
        for order in approved_orders:
            supplier_counts[order.supplier] = supplier_counts.get(order.supplier, 0) + 1
        best_supplier = max(supplier_counts, key=supplier_counts.get)

        return {
            "total_orders": len(approved_orders),
            "total_spent": round(total_spent, 2),
            "best_supplier": best_supplier,
            "confirmed_orders": len(confirmed_orders)
        }
    finally:
        db.close()