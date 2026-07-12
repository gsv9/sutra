from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
import concurrent.futures
from pydantic import BaseModel

from config import HOST, PORT, USE_REAL_CLOUD
from database import create_tables, seed_demo_data, SessionLocal, Inventory, ProcurementOrder
from serial_listener import start_listening
from cloud_sync import start_cloud_sync
from websocket_manager import (
    manager,
    broadcast_recommendation,
    broadcast_inventory_update,
    broadcast_order_to_supplier,
    broadcast_supplier_confirmation
)
import agent_bridge
import procurement_engine

# 1. HARDWARE ISOLATION: Create a separate OS-level process for the Snapdragon NPU
# This completely bypasses the Python GIL so WebSockets never drop.
ai_executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)

def connect_modules():
    async def on_recommendation(result):
        await broadcast_recommendation(result)

    agent_bridge.on_recommendation_ready = on_recommendation
    procurement_engine.broadcast_to_supplier = broadcast_order_to_supplier
    procurement_engine.broadcast_to_owner = manager.broadcast_to_dashboard
    print("[MAIN] All modules connected")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("  SUTRA Backend Starting...")
    print("="*50)

    create_tables()
    seed_demo_data()
    connect_modules()

    main_loop = asyncio.get_running_loop()

    def handle_event(event):
        # Schedule the AI task onto the async loop safely from the serial thread
        asyncio.run_coroutine_threadsafe(run_agent(event), main_loop)

    async def run_agent(event):
        try:
            # Execute the 30-second NPU block in the isolated process pool
            result = await main_loop.run_in_executor(
                ai_executor, 
                agent_bridge.handle_arduino_event, 
                event
            )
            if result and agent_bridge.on_recommendation_ready:
                await agent_bridge.on_recommendation_ready(result)
        except Exception as e:
            print(f"[AGENT THREAD ERROR] {e}")

    start_listening(handle_event)

    if USE_REAL_CLOUD:
        start_cloud_sync()
    else:
        print("[MAIN] Cloud sync disabled for demo mode")

    print("\n[MAIN] SUTRA Backend is ready!")
    print(f"[MAIN] Dashboard: http://{HOST}:{PORT}")
    print("="*50 + "\n")
    
    yield
    
    print("\n[MAIN] SUTRA Backend shutting down...")
    ai_executor.shutdown(wait=True)


app = FastAPI(title="SUTRA Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    loop = asyncio.get_running_loop()
    # Route voice conversation to the isolated NPU process
    answer = await loop.run_in_executor(
        ai_executor, 
        agent_bridge.chat_with_phi3, 
        req.question
    )
    return {"answer": answer}


@app.get("/")
def root():
    return {"name": "SUTRA Backend", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/inventory")
def get_inventory():
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
                    "status": "critical" if item.current_weight <= item.reorder_threshold else "healthy",
                    "last_updated": str(item.last_updated)
                } for item in items
            ]
        }
    finally:
        db.close()

@app.post("/inventory/update")
async def update_inventory(data: dict):
    db = SessionLocal()
    try:
        item = db.query(Inventory).filter(Inventory.item_name == data["item_name"]).first()
        if item:
            item.current_weight = data["current_weight"]
            item.last_updated = datetime.now()
            db.commit()

        inventory = db.query(Inventory).all()
        await broadcast_inventory_update([
            {
                "item_name": i.item_name,
                "current_weight": i.current_weight,
                "reorder_threshold": i.reorder_threshold,
                "unit": i.unit
            } for i in inventory
        ])
        return {"status": "updated"}
    finally:
        db.close()

@app.post("/procurement/approve")
async def approve_procurement(data: dict):
    result = await procurement_engine.execute_procurement(data)
    return {"status": "approved", "po_number": result["po_number"]}

@app.post("/procurement/reject")
async def reject_procurement(data: dict):
    rejected_po = procurement_engine.handle_rejection(data, data.get("reason", "Owner rejected"))
    await manager.broadcast_to_dashboard({
        "type": "recommendation_rejected",
        "po_number": rejected_po,
        "timestamp": datetime.now().isoformat()
    })
    return {"status": "rejected", "po_number": rejected_po}

@app.get("/procurement/orders")
def get_orders():
    db = SessionLocal()
    try:
        orders = db.query(ProcurementOrder).order_by(ProcurementOrder.id.desc()).all()
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
                } for o in orders
            ]
        }
    finally:
        db.close()

@app.post("/supplier/confirm")
async def supplier_confirm(data: dict):
    original_order = procurement_engine.get_order(data["po_number"])
    if not original_order:
        return {"status": "error", "message": "Order not found"}

    confirmed_po = procurement_engine.generate_po_number()
    procurement_engine.save_recommendation_to_db(
        po_number=confirmed_po,
        item=original_order.item,
        recommendation={
            "quantity": original_order.quantity,
            "supplier": original_order.supplier,
            "unit_price": original_order.unit_price,
            "total_cost": original_order.total_cost,
            "savings": original_order.savings,
            "reasoning": original_order.reasoning,
        },
        status="confirmed",
        expected_delivery=data.get("confirmed_delivery", original_order.expected_delivery)
    )

    order_data = {
        "po_number": confirmed_po,
        "supplier": original_order.supplier,
        "item": original_order.item,
        "quantity": original_order.quantity,
        "expected_delivery": data.get("confirmed_delivery", original_order.expected_delivery)
    }
    await broadcast_supplier_confirmation(order_data)
    return {"status": "confirmed", "po_number": confirmed_po}

@app.post("/supplier/reject")
def supplier_reject(data: dict):
    original_order = procurement_engine.get_order(data["po_number"])
    if not original_order:
        return {"status": "error"}

    rejected_po = procurement_engine.generate_po_number()
    procurement_engine.save_recommendation_to_db(
        po_number=rejected_po,
        item=original_order.item,
        recommendation={
            "quantity": original_order.quantity,
            "supplier": original_order.supplier,
            "unit_price": original_order.unit_price,
            "total_cost": original_order.total_cost,
            "savings": original_order.savings,
            "reasoning": original_order.reasoning,
        },
        status="supplier_rejected"
    )
    return {"status": "supplier_rejected"}

@app.post("/conversation/ask")
async def ask_question(data: dict):
    """
    Answers a follow-up question about the most recent recommendation.
    Runs Phi-3 chat() in a background thread so it doesn't block the
    event loop, same fix as the main inference path.
    """
    question = (data.get("question") or "").strip()
    if not question:
        return {"answer": "", "status": "empty_question"}

    try:
        import sys
        from pathlib import Path
        from config import ML_PROJECT_ROOT

        ml_root = Path(ML_PROJECT_ROOT)
        if ml_root.exists():
            ml_root_str = str(ml_root)
            if ml_root_str not in sys.path:
                sys.path.insert(0, ml_root_str)

        from ml.agent import get_conversation_memory, chat
        from ml.schemas import AgentState
        from ml.feature_engineering import FeatureEngineer

        memory = get_conversation_memory()

        if memory.recommendation is None or memory.context is None:
            return {"answer": "No recommendation is active yet.", "status": "no_context"}

        engineered = FeatureEngineer.compute(memory.context)
        state = AgentState(
            recommendation=memory.recommendation,
            engineered_context=engineered,
        )

        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            None, chat, question, state, memory.context
        )

        return {"answer": answer, "status": "ok"}

    except Exception as exc:
        print(f"[CONVERSATION] Failed: {exc}")
        return {"answer": "Sorry, I couldn't process that question right now.", "status": "error"}

@app.get("/analytics/summary")
def get_analytics():
    return procurement_engine.get_analytics_summary()

@app.get("/analytics/insights")
def get_cloud_insights():
    from cloud_sync import get_insights
    return get_insights()

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await manager.connect_dashboard(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_dashboard(websocket)

@app.websocket("/ws/mobile")
async def websocket_mobile(websocket: WebSocket):
    await manager.connect_mobile(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_mobile(websocket)

@app.websocket("/ws/supplier")
async def websocket_supplier(websocket: WebSocket):
    await manager.connect_supplier(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_supplier(websocket)


if __name__ == "__main__":
    import uvicorn
    # Execution MUST be strictly bound via 0.0.0.0 directly from __main__ to support ProcessPoolExecutor
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)