import { useState, useEffect } from 'react';

export function useSutraSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [inventory, setInventory] = useState([]);
  const [recommendation, setRecommendation] = useState(null);
  const [confirmedOrders, setConfirmedOrders] = useState([]);

  useEffect(() => {
    let ws;
    let reconnectTimeout;

    const connect = () => {
      ws = new WebSocket('ws://localhost:8000/ws/dashboard');
      
      ws.onopen = () => setIsConnected(true);
      
      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connect, 3000); 
      };

      ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'inventory_update') {
            setInventory(data.inventory);
          }
          if (data.type === 'new_recommendation') {
            setRecommendation(data);
          }
          if (data.type === 'clear_recommendation') {
            setRecommendation(null);
          }
          if (data.type === 'order_confirmed') {
            const orderPayload = data.order || data;
            if (orderPayload) {
              setConfirmedOrders((prev) => {
                // Strict deduplication lock. Discards duplicate PO broadcasts.
                if (prev.some(order => order.po_number === orderPayload.po_number)) {
                  return prev;
                }
                return [orderPayload, ...prev];
              });
              setRecommendation(null);
            }
          }
        } catch (err) {
          console.error("Failed to parse payload:", err);
        }
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, []);

  return { isConnected, inventory, recommendation, confirmedOrders };
}