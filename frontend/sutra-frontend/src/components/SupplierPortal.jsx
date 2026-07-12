import { useState, useEffect } from 'react';
import { Package, Check, X, Truck, Building2, Lock, Calendar } from 'lucide-react';
import { apiUrl, wsUrl } from '../lib/config';

export default function SupplierPortal() {
  const [orders, setOrders] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [deliveryDates, setDeliveryDates] = useState({});

  useEffect(() => {
    let ws;
    let reconnectTimeout;

    const connect = () => {
      ws = new WebSocket(wsUrl('/ws/supplier'));

      ws.onopen = () => setIsConnected(true);

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connect, 3000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'new_order') {
            setOrders((prev) => {
              if (prev.some((order) => order.po_number === data.po_number)) {
                return prev;
              }
              return [data, ...prev];
            });
          }
        } catch (err) {
          console.error('Failed to parse supplier payload:', err);
        }
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, []);

  const handleDateChange = (po_number, date) => {
    setDeliveryDates((prev) => ({ ...prev, [po_number]: date }));
  };

  const handleOrderResponse = async (po_number, action) => {
    try {
      const endpoint = action === 'confirm' ? '/supplier/confirm' : '/supplier/reject';
      const defaultDate = new Date(Date.now() + 86400000).toISOString().split('T')[0];
      const confirmedDate = deliveryDates[po_number] || defaultDate;

      await fetch(apiUrl(endpoint), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ po_number, confirmed_delivery: confirmedDate }),
      });

      setOrders((prev) => prev.filter((order) => order.po_number !== po_number));
    } catch (err) {
      console.error('Failed to transmit supplier response:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto mb-8 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
            <Building2 className="w-6 h-6 text-emerald-700" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Supplier Operations Portal</h1>
            <div className="flex items-center gap-2 mt-1">
              <Lock className="w-3 h-3 text-emerald-600" />
              <p className="text-emerald-700 text-xs font-bold">256-bit E2E Encrypted Network</p>
            </div>
          </div>
        </div>
        <div
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold shadow-sm ${
            isConnected ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
          }`}
        >
          <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
          {isConnected ? 'NETWORK ACTIVE' : 'DISCONNECTED'}
        </div>
      </div>

      <div className="max-w-5xl mx-auto">
        <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Package className="w-5 h-5 text-slate-500" />
          Incoming Purchase Orders
        </h2>

        {orders.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 border-dashed p-12 flex flex-col items-center justify-center text-slate-400">
            <Truck className="w-12 h-12 mb-3 opacity-20" />
            <p className="font-medium">No pending orders in the queue.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {orders.map((order) => (
              <div key={order.po_number} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="border-b border-slate-100 bg-slate-50 p-4 flex justify-between items-center">
                  <span className="font-mono text-xs font-bold text-slate-500">{order?.po_number || 'UNKNOWN-PO'}</span>
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-bold rounded uppercase tracking-wider">
                    Requires Action
                  </span>
                </div>

                <div className="p-5 space-y-4">
                  <div>
                    <div className="text-sm text-slate-500 font-medium mb-1">Client</div>
                    <div className="font-bold text-slate-900">{order?.from_store || 'Retail Partner'}</div>
                  </div>

                  <div className="flex justify-between items-end">
                    <div>
                      <div className="text-sm text-slate-500 font-medium mb-1">Requested Item</div>
                      <div className="text-xl font-black text-slate-800">
                        {order?.quantity || 0}kg {order?.item || 'Item'}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-slate-500 font-medium mb-1">Total Value</div>
                      <div className="text-lg font-bold text-emerald-600">₹{order?.total_cost || 0}</div>
                    </div>
                  </div>

                  <div className="pt-2">
                    <label className="text-xs font-bold text-slate-500 mb-1 flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> Target Delivery Date
                    </label>
                    <input
                      type="date"
                      onChange={(e) => handleDateChange(order.po_number, e.target.value)}
                      className="w-full border border-slate-200 rounded p-2 text-sm text-slate-700 outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100 mt-4">
                    <button
                      onClick={() => handleOrderResponse(order.po_number, 'reject')}
                      className="flex items-center justify-center gap-2 py-2.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50 font-bold transition-colors"
                    >
                      <X className="w-4 h-4" /> Decline
                    </button>
                    <button
                      onClick={() => handleOrderResponse(order.po_number, 'confirm')}
                      className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-sm transition-colors"
                    >
                      <Check className="w-4 h-4" /> Confirm Order
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
