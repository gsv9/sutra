# websocket_manager.py
# Manages real-time WebSocket connections to all frontends
# Pushes live updates to owner dashboard, mobile app, supplier portal

from fastapi import WebSocket
from typing import List
import json
from datetime import datetime


# ─── CONNECTION MANAGER ───────────────────────────────────────

class ConnectionManager:
    """
    Manages all active WebSocket connections.
    Keeps separate lists for each frontend type.
    """

    def __init__(self):
        # List of connected owner dashboards
        self.dashboard_connections: List[WebSocket] = []

        # List of connected mobile apps
        self.mobile_connections: List[WebSocket] = []

        # List of connected supplier portals
        self.supplier_connections: List[WebSocket] = []

    # ── CONNECT ──────────────────────────────────────────────

    async def connect_dashboard(self, websocket: WebSocket):
        await websocket.accept()
        self.dashboard_connections.append(websocket)
        print(f"[WS] Owner dashboard connected. Total: {len(self.dashboard_connections)}")

    async def connect_mobile(self, websocket: WebSocket):
        await websocket.accept()
        self.mobile_connections.append(websocket)
        print(f"[WS] Mobile app connected. Total: {len(self.mobile_connections)}")

    async def connect_supplier(self, websocket: WebSocket):
        await websocket.accept()
        self.supplier_connections.append(websocket)
        print(f"[WS] Supplier portal connected. Total: {len(self.supplier_connections)}")

    # ── DISCONNECT ────────────────────────────────────────────

    def disconnect_dashboard(self, websocket: WebSocket):
        self.dashboard_connections.remove(websocket)
        print(f"[WS] Owner dashboard disconnected")

    def disconnect_mobile(self, websocket: WebSocket):
        if websocket in self.mobile_connections:
            self.mobile_connections.remove(websocket)
            print(f"[WS] Mobile app disconnected")

    def disconnect_supplier(self, websocket: WebSocket):
        if websocket in self.supplier_connections:
            self.supplier_connections.remove(websocket)
            print(f"[WS] Supplier portal disconnected")

    # ── BROADCAST TO ALL DASHBOARDS ───────────────────────────

    async def broadcast_to_dashboard(self, message: dict):
        """
        Sends message to all connected owner dashboards.
        """
        disconnected = []

        for websocket in self.dashboard_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                # Connection dropped — mark for removal
                disconnected.append(websocket)

        # Clean up dropped connections
        for ws in disconnected:
            self.dashboard_connections.remove(ws)

    # ── BROADCAST TO ALL MOBILE APPS ──────────────────────────

    async def broadcast_to_mobile(self, message: dict):
        """
        Sends message to all connected mobile apps.
        """
        disconnected = []

        for websocket in self.mobile_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for ws in disconnected:
            self.mobile_connections.remove(ws)

    # ── BROADCAST TO ALL SUPPLIER PORTALS ─────────────────────

    async def broadcast_to_supplier(self, message: dict):
        """
        Sends message to all connected supplier portals.
        """
        disconnected = []

        for websocket in self.supplier_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for ws in disconnected:
            self.supplier_connections.remove(ws)


# ─── SINGLE INSTANCE ──────────────────────────────────────────
# One manager shared across the entire application
manager = ConnectionManager()


# ─── BROADCAST RECOMMENDATION ─────────────────────────────────

async def broadcast_recommendation(result: dict):
    """
    Called by agent_bridge when AI recommendation is ready.
    Sends different messages to different frontends.
    """

    recommendation = result["recommendation"]
    event = result["event"]

    # ── Message for Owner Dashboard ──
    # Full detailed view with reasoning
    dashboard_message = {
        "type": "new_recommendation",
        "item": event["item"],
        "remaining_weight": event["remaining_weight"],
        "event_type": event["event"],
        "recommendation": recommendation["recommendation"],
        "supplier": recommendation["supplier"],
        "quantity": recommendation["quantity"],
        "total_cost": recommendation["total_cost"],
        "savings": recommendation["savings"],
        "reasoning": recommendation["reasoning"],
        "confidence": recommendation["confidence"],
        "status": "pending_approval",
        "timestamp": result["timestamp"]
    }

    # ── Message for Mobile App ──
    # Simplified notification format
    mobile_message = {
        "type": "approval_request",
        "item": event["item"],
        "quantity": recommendation["quantity"],
        "supplier": recommendation["supplier"],
        "savings": recommendation["savings"],
        "total_cost": recommendation["total_cost"],
        "expected_delivery_days": recommendation["expected_delivery_days"],
        "status": "pending_approval",
        "timestamp": result["timestamp"]
    }

    # Send to all connected frontends
    await manager.broadcast_to_dashboard(dashboard_message)
    await manager.broadcast_to_mobile(mobile_message)

    print(f"[WS] Recommendation broadcast to all frontends")


# ─── BROADCAST INVENTORY UPDATE ───────────────────────────────

async def broadcast_inventory_update(inventory_data: list):
    """
    Sends current inventory levels to dashboard.
    Called when Arduino updates weight readings.
    """
    message = {
        "type": "inventory_update",
        "inventory": inventory_data,
        "timestamp": datetime.now().isoformat()
    }

    await manager.broadcast_to_dashboard(message)


# ─── BROADCAST SUPPLIER CONFIRMATION ──────────────────────────

async def broadcast_supplier_confirmation(order_data: dict):
    """
    Sends order confirmation to owner dashboard and mobile.
    Called when supplier confirms an order.
    """

    # Tell owner their order is confirmed
    owner_message = {
        "type": "order_confirmed",
        "po_number": order_data["po_number"],
        "supplier": order_data["supplier"],
        "item": order_data["item"],
        "quantity": order_data["quantity"],
        "expected_delivery": order_data["expected_delivery"],
        "timestamp": datetime.now().isoformat()
    }

    await manager.broadcast_to_dashboard(owner_message)
    await manager.broadcast_to_mobile(owner_message)

    print(f"[WS] Supplier confirmation broadcast to owner")


# ─── BROADCAST NEW ORDER TO SUPPLIER ──────────────────────────

async def broadcast_order_to_supplier(order_data: dict):
    """
    Sends new purchase order to supplier portal.
    Called when owner approves a recommendation.
    """
    supplier_message = {
        "type": "new_order",
        "po_number": order_data["po_number"],
        "from_store": "Lakshmi Stores, Coimbatore",
        "item": order_data["item"],
        "quantity": order_data["quantity"],
        "required_by": order_data["expected_delivery"],
        "total_cost": order_data["total_cost"],
        "timestamp": datetime.now().isoformat()
    }

    await manager.broadcast_to_supplier(supplier_message)
    print(f"[WS] New order sent to supplier portal")