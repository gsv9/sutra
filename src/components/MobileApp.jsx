import { useState, useEffect } from 'react';
import { useSutraSocket } from '../hooks/useSutraSocket';
import { Smartphone, ShieldCheck, Zap, XCircle } from 'lucide-react';

export default function MobileApp() {
  const { isConnected, recommendation } = useSutraSocket();
  const [localRecommendation, setLocalRecommendation] = useState(null);
  const [actionStatus, setActionStatus] = useState(null);

  useEffect(() => {
    if (recommendation) {
      setLocalRecommendation(recommendation);
      setActionStatus(null);
    }
  }, [recommendation]);

  const handleAction = async (status) => {
    if (!localRecommendation) return;
    
    setActionStatus(status);
    
    // Construct payload strictly matching procurement_engine requirements
    const payload = {
      po_number: localRecommendation.po_number || `MOCK-${Date.now()}`,
      action: status,
      item: localRecommendation.item || localRecommendation.event?.item,
      supplier: localRecommendation.supplier,
      quantity: localRecommendation.quantity || 30,
      savings: localRecommendation.savings || 0,
      total_cost: localRecommendation.total_cost || 0,
      unit_price: localRecommendation.total_cost ? parseFloat((localRecommendation.total_cost / localRecommendation.quantity).toFixed(2)) : 0,
      expected_delivery_days: localRecommendation.expected_delivery_days || 2,
      reasoning: localRecommendation.reasoning || "Approved by owner via SUTRA Mobile"
    };

    try {
      // Direct REST API fall-through. 
      // NOTE: If testing on a physical phone, change 'localhost' to your PC's IPv4 address.
      const endpoint = status === 'approved' ? '/procurement/approve' : '/procurement/reject';
      await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (err) {
      console.error(`Failed to dispatch mobile action:`, err);
    }

    // Auto-clear card after animation window
    setTimeout(() => {
      setLocalRecommendation(null);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4 antialiased font-sans">
      
      {/* Device Wrapper frame */}
      <div className="w-full max-w-[380px] h-[760px] bg-black rounded-[48px] p-3 shadow-2xl border-4 border-slate-800 relative flex flex-col overflow-hidden">
        
        {/* Device Notch */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 w-32 h-5 bg-black rounded-b-2xl z-50 flex items-center justify-center">
          <div className="w-3 h-3 rounded-full bg-slate-900 absolute left-4"></div>
          <div className="w-12 h-1 bg-slate-800 rounded-full"></div>
        </div>

        {/* Core Mobile Screen Area */}
        <div className="flex-1 bg-slate-950 rounded-[38px] overflow-hidden flex flex-col p-5 pt-8 relative">
          
          {/* App Header Status */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-1.5">
              <Smartphone className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-bold text-slate-400 tracking-wider">SUTRA Go</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></span>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                {isConnected ? 'Live Sync' : 'Offline'}
              </span>
            </div>
          </div>

          {/* Main Content Pane */}
          <div className="flex-1 flex flex-col justify-center">
            {localRecommendation ? (
              <div className={`bg-slate-900 rounded-2xl border border-slate-800 p-5 transition-all duration-500 transform ${
                actionStatus === 'approved' ? 'scale-95 translate-y-[-20px] opacity-0 border-emerald-500' : 
                actionStatus === 'rejected' ? 'scale-95 translate-y-[20px] opacity-0 border-red-500' : 'scale-100 opacity-100'
              }`}>
                {/* AI Badge Banner */}
                <div className="flex items-center gap-2 mb-4 bg-blue-950/50 border border-blue-900/40 rounded-xl px-3 py-2">
                  <Zap className="w-4 h-4 text-blue-400 fill-blue-400" />
                  <span className="text-xs font-bold text-blue-400 tracking-wide uppercase">Snapdragon NPU Decision</span>
                </div>

                {/* Main Recommendation Text */}
                <h3 className="text-lg font-bold text-white mb-2 leading-snug">
                  {localRecommendation.recommendation}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4 italic">
                  "{localRecommendation.reasoning}"
                </p>

                {/* Metrics Breakdown */}
                <div className="space-y-2 border-t border-b border-slate-800/60 py-3 mb-6">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">Supplier Target</span>
                    <span className="font-semibold text-slate-200">{localRecommendation.supplier}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">Confidence Score</span>
                    <span className="font-semibold text-blue-400">{localRecommendation.confidence || 95}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">Optimized Margin</span>
                    <span className="font-bold text-emerald-400">₹{localRecommendation.savings} saved</span>
                  </div>
                </div>

                {/* Action Controls */}
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={() => handleAction('rejected')}
                    className="flex items-center justify-center gap-1.5 py-3 rounded-xl bg-slate-800 hover:bg-red-950/30 text-slate-300 hover:text-red-400 font-bold text-xs border border-slate-700/60 transition-all active:scale-95"
                  >
                    <XCircle className="w-4 h-4" />
                    Deny
                  </button>
                  <button 
                    onClick={() => handleAction('approved')}
                    className="flex items-center justify-center gap-1.5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-600/10 transition-all active:scale-95"
                  >
                    <ShieldCheck className="w-4 h-4" />
                    Approve
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 px-4 animate-fade-in">
                <div className="w-14 h-14 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-4">
                  <ShieldCheck className="w-6 h-6 text-slate-600" />
                </div>
                <h4 className="text-sm font-bold text-slate-300">Operational Grid Clear</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-[200px] mx-auto">
                  No pending procurement vectors require immediate executive authorization.
                </p>
              </div>
            )}
          </div>

          {/* Persistent Device Navigation Anchor Bar */}
          <div className="mt-auto pt-4 border-t border-slate-900/60 flex justify-center">
            <div className="w-28 h-1 bg-slate-700 rounded-full"></div>
          </div>

        </div>
      </div>
    </div>
  );
}