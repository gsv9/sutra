
import { useSutraSocket } from '../hooks/useSutraSocket';
import { Box, Zap, ShoppingCart, CheckCircle, AlertTriangle } from 'lucide-react';

export default function Dashboard() {
  const { isConnected, inventory, recommendation, confirmedOrders } = useSutraSocket();

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans">
      {/* Top Navigation / Status Bar */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">SUTRA Operations</h1>
          <p className="text-slate-500 text-sm mt-1">Real-time hardware telemetry & AI procurement</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold shadow-sm ${isConnected ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
          <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
          {isConnected ? 'NODE CONNECTED' : 'SYSTEM OFFLINE'}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Column: Live Inventory */}
        <div className="xl:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
          <div className="flex items-center gap-2 mb-6 border-b border-slate-50 pb-4">
            <Box className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-800">Live Hardware Telemetry</h2>
          </div>
          
          {inventory && inventory.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {inventory.map((item, idx) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-100 bg-slate-50">
                  <div className="text-sm font-semibold text-slate-500 uppercase tracking-wider">{item.item_name}</div>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-3xl font-black text-slate-900">{item.current_weight.toFixed(1)}</span>
                    <span className="text-slate-500 font-medium">{item.unit}</span>
                  </div>
                  <div className="mt-3 text-xs font-medium px-2 py-1 bg-white rounded text-slate-500 inline-block border border-slate-200">
                    Threshold: {item.reorder_threshold}{item.unit}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <AlertTriangle className="w-8 h-8 mb-2 opacity-50" />
              <p>Waiting for Arduino telemetry payload...</p>
            </div>
          )}
        </div>

        {/* Right Column: AI Engine & Orders */}
        <div className="space-y-6">
          
          {/* AI Recommendation Panel */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-blue-500"></div>
            <div className="flex items-center gap-2 mb-6">
              <Zap className="w-5 h-5 text-blue-500 fill-blue-500" />
              <h2 className="text-xl font-bold text-slate-800">AI Agent Engine</h2>
            </div>

            {recommendation ? (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="bg-blue-50 rounded-xl p-4 mb-4 border border-blue-100">
                  <div className="flex justify-between items-start mb-2">
                    <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded uppercase">Action Required</span>
                    <span className="text-blue-700 font-bold text-sm">Confidence: {recommendation.confidence}%</span>
                  </div>
                  <p className="text-slate-800 font-medium">{recommendation.recommendation}</p>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-500">Trigger Event:</span>
                    <span className="font-semibold text-slate-800">{recommendation.event_type}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-500">Target Supplier:</span>
                    <span className="font-semibold text-slate-800">{recommendation.supplier}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-500">Projected Savings:</span>
                    <span className="font-bold text-emerald-600">₹{recommendation.savings}</span>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-slate-50 rounded text-sm text-slate-600 italic border-l-2 border-blue-300">
                  " {recommendation.reasoning} "
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-slate-400">
                <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center mb-3">
                  <Zap className="w-6 h-6 text-slate-300" />
                </div>
                <p className="text-sm font-medium">System Idle</p>
                <p className="text-xs mt-1">Monitoring consumption patterns</p>
              </div>
            )}
          </div>

          {/* Activity Log */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div className="flex items-center gap-2 mb-4">
              <ShoppingCart className="w-5 h-5 text-emerald-600" />
              <h2 className="text-lg font-bold text-slate-800">Confirmed Orders</h2>
            </div>
            
            <div className="space-y-3">
              {confirmedOrders.length > 0 ? (
                confirmedOrders.map((order, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-emerald-500" />
                      <div>
                        <div className="font-semibold text-slate-800 text-sm">{order.item} from {order.supplier}</div>
                        <div className="text-xs text-slate-500 font-mono">{order.po_number}</div>
                      </div>
                    </div>
                    <div className="font-bold text-slate-700 text-sm">{order.quantity}kg</div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-sm text-slate-400">No recent orders</div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}