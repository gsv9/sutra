import { useState, useEffect, useRef } from 'react';
import { useSutraSocket } from '../hooks/useSutraSocket';
import { Smartphone, ShieldCheck, Zap, XCircle, Mic, Lock, BarChart2, Loader2, Globe } from 'lucide-react';

const translations = {
  en: {
    app_name: "SUTRA Go",
    mtd_spend: "MTD Spend",
    suppliers_active: "Suppliers Active",
    decision: "Snapdragon NPU Decision",
    target: "Supplier Target",
    confidence: "Confidence Score",
    savings: "Optimized Margin",
    saved: "saved",
    deny: "Deny",
    approve: "Approve",
    grid_clear: "Operational Grid Clear"
  },
  hi: {
    app_name: "सूत्र गो",
    mtd_spend: "मासिक खर्च",
    suppliers_active: "सक्रिय आपूर्तिकर्ता",
    decision: "स्नैपड्रैगन NPU निर्णय",
    target: "लक्षित आपूर्तिकर्ता",
    confidence: "विश्वास स्कोर",
    savings: "अनुकूलित मार्जिन",
    saved: "बचत",
    deny: "अस्वीकार",
    approve: "मंजूर",
    grid_clear: "परिचालन ग्रिड स्पष्ट"
  },
  ta: {
    app_name: "சூத்ரா கோ",
    mtd_spend: "மாதாந்திர செலவு",
    suppliers_active: "செயலில் உள்ளவர்கள்",
    decision: "Snapdragon NPU முடிவு",
    target: "இலக்கு நிறுவனம்",
    confidence: "நம்பிக்கை மதிப்பெண்",
    savings: "சேமிப்பு",
    saved: "சேமிக்கப்பட்டது",
    deny: "நிராகரி",
    approve: "ஒப்புக்கொள்",
    grid_clear: "காத்திருப்பு இல்லை"
  }
};

export default function MobileApp() {
  const { isConnected, recommendation, confirmedOrders } = useSutraSocket();
  const [localRecommendation, setLocalRecommendation] = useState(null);
  const [actionStatus, setActionStatus] = useState(null);
  const [lang, setLang] = useState('en');
  
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    if (recommendation) {
      setLocalRecommendation(recommendation);
      setActionStatus(null);
    }
  }, [recommendation]);

  const baseMtdSpend = 42500;
  const currentMtdSpend = baseMtdSpend + confirmedOrders.reduce((total, order) => total + (order?.total_cost || 0), 0);
  const t = translations[lang];

  const cycleLanguage = () => {
    if (lang === 'en') setLang('hi');
    else if (lang === 'hi') setLang('ta');
    else setLang('en');
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        stream.getTracks().forEach(track => track.stop());

        const formData = new FormData();
        formData.append('audio', audioBlob, 'query.wav');
        formData.append('language', lang);

        try {
          const response = await fetch('http://localhost:8000/voice/process', {
            method: 'POST',
            body: formData,
          });
          
          if (response.ok) {
            const audioResponseBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioResponseBlob);
            const audio = new Audio(audioUrl);
            audio.play();
          } else {
            console.error("Backend rejected audio payload.");
          }
        } catch (error) {
          console.error("Audio transmission failed:", error);
        } finally {
          setIsProcessing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone hardware access denied:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleAction = async (status) => {
    if (!localRecommendation) return;
    setActionStatus(status);
    
    if (!localRecommendation.quantity) console.warn("SUTRA ALERT: 'quantity' missing from AI payload. Defaulting to 30.");
    if (!localRecommendation.total_cost) console.warn("SUTRA ALERT: 'total_cost' missing from AI payload. Defaulting to demo value.");
    if (!localRecommendation.confidence) console.warn("SUTRA ALERT: 'confidence' missing. UI showing default 95%.");

    const payload = {
      po_number: localRecommendation.po_number || `PENDING-${Date.now()}`,
      action: status,
      item: localRecommendation.item || localRecommendation.event?.item,
      supplier: localRecommendation.supplier,
      quantity: localRecommendation.quantity || 30,
      savings: localRecommendation.savings || 0,
      total_cost: localRecommendation.total_cost || 1200,
      unit_price: localRecommendation.total_cost ? parseFloat((localRecommendation.total_cost / localRecommendation.quantity).toFixed(2)) : 40.0,
      expected_delivery_days: localRecommendation.expected_delivery_days || 2,
      reasoning: localRecommendation.reasoning || "Approved by owner via SUTRA Mobile"
    };

    try {
      const endpoint = status === 'approved' ? '/procurement/approve' : '/procurement/reject';
      await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (err) {
      console.error(`Failed to dispatch mobile action:`, err);
    }

    setTimeout(() => {
      setLocalRecommendation(null);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4 antialiased font-sans">
      <div className="w-full max-w-[380px] h-[760px] bg-black rounded-[48px] p-3 shadow-2xl border-4 border-slate-800 relative flex flex-col overflow-hidden">
        
        <div className="absolute top-3 left-1/2 -translate-x-1/2 w-32 h-5 bg-black rounded-b-2xl z-50 flex items-center justify-center">
          <div className="w-3 h-3 rounded-full bg-slate-900 absolute left-4"></div>
          <div className="w-12 h-1 bg-slate-800 rounded-full"></div>
        </div>

        <div className="flex-1 bg-slate-950 rounded-[38px] overflow-hidden flex flex-col p-5 pt-8 relative">
          
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-1.5">
              <Smartphone className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-bold text-slate-400 tracking-wider">{t.app_name}</span>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={cycleLanguage} className="flex items-center gap-1 text-[10px] font-bold text-slate-400 bg-slate-800 px-2 py-1 rounded-full hover:bg-slate-700 transition-colors uppercase">
                <Globe className="w-3 h-3" /> {lang}
              </button>
              <div className="flex items-center gap-1.5">
                <Lock className="w-3 h-3 text-slate-500" />
                <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></span>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center bg-slate-900 border border-slate-800 rounded-xl p-3 mb-6">
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                <BarChart2 className="w-3 h-3"/> {t.mtd_spend}
              </div>
              <div className="text-white font-bold text-sm">
                ₹ {currentMtdSpend.toLocaleString('en-IN')}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-500 uppercase font-bold">{t.suppliers_active}</div>
              <div className="text-emerald-400 font-bold text-sm">4 / 4</div>
            </div>
          </div>

          <div className="flex-1 flex flex-col justify-center relative">
            {localRecommendation ? (
              <div className={`bg-slate-900 rounded-2xl border border-slate-800 p-5 transition-all duration-500 transform ${
                actionStatus === 'approved' ? 'scale-95 translate-y-[-20px] opacity-0 border-emerald-500' : 
                actionStatus === 'rejected' ? 'scale-95 translate-y-[20px] opacity-0 border-red-500' : 'scale-100 opacity-100'
              }`}>
                <div className="flex items-center gap-2 mb-4 bg-blue-950/50 border border-blue-900/40 rounded-xl px-3 py-2">
                  <Zap className="w-4 h-4 text-blue-400 fill-blue-400" />
                  <span className="text-xs font-bold text-blue-400 tracking-wide uppercase">{t.decision}</span>
                </div>

                <h3 className="text-lg font-bold text-white mb-2 leading-snug">{localRecommendation.recommendation}</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4 italic">"{localRecommendation.reasoning}"</p>

                <div className="space-y-2 border-t border-b border-slate-800/60 py-3 mb-6">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">{t.target}</span>
                    <span className="font-semibold text-slate-200">{localRecommendation.supplier}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">{t.confidence}</span>
                    <span className="font-semibold text-blue-400">{localRecommendation.confidence || 95}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">{t.savings}</span>
                    <span className="font-bold text-emerald-400">₹{localRecommendation.savings} {t.saved}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <button onClick={() => handleAction('rejected')} className="flex items-center justify-center gap-1.5 py-3 rounded-xl bg-slate-800 hover:bg-red-950/30 text-slate-300 font-bold text-xs border border-slate-700/60 transition-all">
                    <XCircle className="w-4 h-4" /> {t.deny}
                  </button>
                  <button onClick={() => handleAction('approved')} className="flex items-center justify-center gap-1.5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md transition-all">
                    <ShieldCheck className="w-4 h-4" /> {t.approve}
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 px-4">
                <div className="w-14 h-14 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-4">
                  <ShieldCheck className="w-6 h-6 text-slate-600" />
                </div>
                <h4 className="text-sm font-bold text-slate-300">{t.grid_clear}</h4>
              </div>
            )}
            
            {!localRecommendation && (
              <button 
                onPointerDown={startRecording}
                onPointerUp={stopRecording}
                onPointerLeave={stopRecording}
                disabled={isProcessing}
                className={`absolute bottom-4 right-2 w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-all 
                  ${isRecording ? 'bg-red-500 scale-110 shadow-red-500/50' : 
                    isProcessing ? 'bg-slate-700' : 'bg-blue-600 hover:bg-blue-500'}`}
              >
                {isProcessing ? <Loader2 className="w-5 h-5 text-white animate-spin" /> : <Mic className="w-5 h-5 text-white" />}
              </button>
            )}
          </div>

          <div className="mt-auto pt-4 border-t border-slate-900/60 flex justify-center">
            <div className="w-28 h-1 bg-slate-700 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}