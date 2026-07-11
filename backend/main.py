# main.py
# Entry point for SUTRA backend
# Starts FastAPI server, connects all modules together

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

# Import all our modules
from config import HOST, PORT
from database import create_tables, seed_demo_data, SessionLocal, Inventory, ProcurementOrder
from serial_listener import start_listening
from cloud_sync import start_cloud_sync, queue_transaction
from websocket_manager import (
    manager,
    broadcast_recommendation,
    broadcast_inventory_update,
    broadcast_order_to_supplier,
    broadcast_supplier_confirmation
)
import agent_bridge
import procurement_engine


# ─── CONNECT MODULES TOGETHER ─────────────────────────────────

def connect_modules():
    """
    Connects all modules by setting their callback functions.
    This is how modules communicate without circular imports.
    """

    # When agent_bridge has a recommendation ready
    # → broadcast it to all frontends
    async def on_recommendation(result):
        await broadcast_recommendation(result)

    # Set agent_bridge's callback
    agent_bridge.on_recommendation_ready = on_recommendation

    # When procurement_engine needs to notify supplier
    # → broadcast to supplier portal
    procurement_engine.broadcast_to_supplier = broadcast_order_to_supplier

    # When procurement_engine needs to notify owner
    # → broadcast to dashboard and mobile
    procurement_engine.broadcast_to_owner = manager.broadcast_to_dashboard

    print("[MAIN] All modules connected")


# ─── STARTUP AND SHUTDOWN ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on server startup and shutdown.
    """
    # STARTUP
    print("\n" + "="*50)
    print("  SUTRA Backend Starting...")
    print("="*50)

    # Step 1: Create database tables
    create_tables()

    # Step 2: Seed demo data
    seed_demo_data()

    # Step 3: Connect all modules
    connect_modules()

    # Step 4: Start Arduino listener in background
    # Store the event loop BEFORE starting the thread
    main_loop = asyncio.get_event_loop()

    def handle_event(event):
        # Arduino event arrives in a thread
        # Use the stored main loop to run async code
        asyncio.run_coroutine_threadsafe(
            run_agent(event), main_loop
        )

    async def run_agent(event):
        result = agent_bridge.handle_arduino_event(event)
        if result and agent_bridge.on_recommendation_ready:
            await agent_bridge.on_recommendation_ready(result)

    start_listening(handle_event)

    # Step 5: Start cloud sync service
    start_cloud_sync()

    print("\n[MAIN] SUTRA Backend is ready!")
    print(f"[MAIN] Dashboard: http://localhost:{PORT}")
    print(f"[MAIN] API Docs:  http://localhost:{PORT}/docs")
    print("="*50 + "\n")

    yield

    # SHUTDOWN
    print("\n[MAIN] SUTRA Backend shutting down...")


# ─── CREATE FASTAPI APP ───────────────────────────────────────

app = FastAPI(
    title="SUTRA Backend",
    description="Agentic Business Operating System for MSMEs",
    version="1.0.0",
    lifespan=lifespan
)

# Allow frontend to connect from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── BASIC ENDPOINTS ──────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "SUTRA Backend",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ─── INVENTORY ENDPOINTS ──────────────────────────────────────

@app.get("/inventory")
def get_inventory():
    """Returns current inventory levels."""
    db = SessionLocal()
    try:
        items = db.query(Inventory).all()
        return {
            "inventory": [
                {
                    "item_name": item.item_name,
                    "current_weight": item.current_weight,
                    "reorder_threshold": item.reorder_threshold,
                    "unit": item.unit,
                    "status": "critical" if item.current_weight
                    <= item.reorder_threshold else "healthy",
                    "last_updated": str(item.last_updated)
                }
                for item in items
            ]
        }
    finally:
        db.close()


@app.post("/inventory/update")
async def update_inventory(data: dict):
    """
    Called when Arduino sends weight update.
    Updates database and broadcasts to dashboard.
    """
    db = SessionLocal()
    try:
        item = db.query(Inventory).filter(
            Inventory.item_name == data["item_name"]
        ).first()

        if item:
            item.current_weight = data["current_weight"]
            item.last_updated = datetime.now()
            db.commit()

        # Broadcast update to dashboard
        inventory = db.query(Inventory).all()
        await broadcast_inventory_update([
            {
                "item_name": i.item_name,
                "current_weight": i.current_weight,
                "reorder_threshold": i.reorder_threshold,
                "unit": i.unit
            }
            for i in inventory
        ])

        return {"status": "updated"}
    finally:
        db.close()


# ─── PROCUREMENT ENDPOINTS ────────────────────────────────────

@app.post("/procurement/approve")
async def approve_procurement(data: dict):
    """
    Called when owner taps Approve on mobile.
    Executes full procurement workflow.
    """
    print(f"[API] Owner approved procurement for {data['item']}")

    result = await procurement_engine.execute_procurement(data)

    # Queue transaction for Cloud 100 sync
    queue_transaction(result)

    return {
        "status": "approved",
        "po_number": result["po_number"],
        "message": f"Purchase order {result['po_number']} created successfully"
    }


@app.post("/procurement/reject")
def reject_procurement(data: dict):
    """Called when owner taps Reject on mobile."""
    procurement_engine.handle_rejection(
        data["po_number"],
        data.get("reason", "Owner rejected")
    )
    return {
        "status": "rejected",
        "po_number": data["po_number"]
    }


@app.get("/procurement/orders")
def get_orders():
    """Returns all procurement orders."""
    db = SessionLocal()
    try:
        orders = db.query(ProcurementOrder).all()
        return {
            "orders": [
                {
                    "po_number": o.po_number,
                    "item": o.item,
                    "quantity": o.quantity,
                    "supplier": o.supplier,
                    "total_cost": o.total_cost,
                    "savings": o.savings,
                    "status": o.status,
                    "created_at": str(o.created_at),
                    "expected_delivery": o.expected_delivery
                }
                for o in orders
            ]
        }
    finally:
        db.close()


# ─── SUPPLIER ENDPOINTS ───────────────────────────────────────

@app.post("/supplier/confirm")
async def supplier_confirm(data: dict):
    """
    Called when supplier taps Confirm on supplier portal.
    Updates order status and notifies owner.
    """
    print(f"[API] Supplier confirmed order: {data['po_number']}")

    procurement_engine.update_order_status(
        data["po_number"], "confirmed"
    )

    db = SessionLocal()
    try:
        order = db.query(ProcurementOrder).filter(
            ProcurementOrder.po_number == data["po_number"]
        ).first()

        if order:
            order_data = {
                "po_number": order.po_number,
                "supplier": order.supplier,
                "item": order.item,
                "quantity": order.quantity,
                "expected_delivery": data.get(
                    "confirmed_delivery", order.expected_delivery
                )
            }
            await broadcast_supplier_confirmation(order_data)

    finally:
        db.close()

    return {
        "status": "confirmed",
        "po_number": data["po_number"]
    }


@app.post("/supplier/reject")
def supplier_reject(data: dict):
    """Called when supplier taps Reject on supplier portal."""
    procurement_engine.update_order_status(
        data["po_number"], "supplier_rejected"
    )
    return {
        "status": "supplier_rejected",
        "po_number": data["po_number"]
    }


# ─── ANALYTICS ENDPOINTS ──────────────────────────────────────

@app.get("/analytics/summary")
def get_analytics():
    """Returns business summary for dashboard."""
    return procurement_engine.get_analytics_summary()


@app.get("/analytics/insights")
def get_cloud_insights():
    """Returns latest insights from Cloud 100."""
    from cloud_sync import get_insights
    return get_insights()


# ─── WEBSOCKET ENDPOINTS ──────────────────────────────────────

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket for owner dashboard on PC screen."""
    await manager.connect_dashboard(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_dashboard(websocket)


@app.websocket("/ws/mobile")
async def websocket_mobile(websocket: WebSocket):
    """WebSocket for owner mobile app."""
    await manager.connect_mobile(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_mobile(websocket)


@app.websocket("/ws/supplier")
async def websocket_supplier(websocket: WebSocket):
    """WebSocket for supplier portal."""
    await manager.connect_supplier(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_supplier(websocket)


# ─── RUN SERVER ───────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)