import { useState, useEffect } from 'react';

export function useSutraSocket() {
  const [inventory, setInventory] = useState([]);
  const [recommendation, setRecommendation] = useState(null);
  const [confirmedOrders, setConfirmedOrders] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard');

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'inventory_update':
          setInventory(data.inventory);
          break;
        case 'new_recommendation':
          setRecommendation(data);
          break;
        case 'procurement_executed':
          setRecommendation(null);
          break;
        case 'order_confirmed':
          setConfirmedOrders((prev) => [data, ...prev]);
          setRecommendation(null);
          break;
        default:
          console.warn('Unknown message type:', data.type);
      }
    };

    return () => ws.close();
  }, []);

  return { isConnected, inventory, recommendation, confirmedOrders };
}