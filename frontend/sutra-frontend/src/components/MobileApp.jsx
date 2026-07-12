import { useEffect, useRef, useState } from 'react';
import { useSutraSocket } from '../hooks/useSutraSocket';
import { apiUrl, DEMO_SUMMARY, translationUrl } from '../lib/config';
import { SpeechRecognition } from '@capacitor-community/speech-recognition';
import {
  ShieldCheck,
  Zap,
  XCircle,
  Mic,
  Lock,
  Globe,
  Loader2,
  TrendingUp,
  Volume2,
} from 'lucide-react';

const translations = {
  en: {
    app_name: 'SUTRA Go',
    decision: 'Local AI Decision',
    target: 'Target',
    confidence: 'Confidence',
    savings: 'Savings',
    deny: 'Deny',
    approve: 'Approve',
    summary_title: 'Summary',
    total_orders: 'Orders',
    total_savings: 'Savings',
    top_supplier: 'Top Supplier',
    voice_hint: 'Hold the mic and speak: "approve", "reject", "explain" — or ask a question.',
    local_voice: 'Native OS Voice Engine',
    voice_footer: 'Speech stays on the device. No /voice/process upload.',
    transcript: 'Heard',
    translation_ready: 'Translation ready',
    translation_fallback: 'Showing original text',
    idle_title: 'Operations Grid Clear',
    idle_sub: 'Monitoring consumption patterns',
  },
  hi: {
    app_name: 'सूत्र गो',
    decision: 'स्थानीय एआई निर्णय',
    target: 'लक्ष्य',
    confidence: 'विश्वास',
    savings: 'बचत',
    deny: 'अस्वीकार',
    approve: 'स्वीकृत',
    summary_title: 'सारांश',
    total_orders: 'आदेश',
    total_savings: 'बचत',
    top_supplier: 'शीर्ष आपूर्तिकर्ता',
    voice_hint: 'माइक दबाकर बोलें: "approve", "reject", "explain" — या कोई सवाल पूछें।',
    local_voice: 'डिवाइस पर मूल वॉयस इंजन',
    voice_footer: 'आवाज़ डिवाइस पर रहती है। /voice/process अपलोड नहीं।',
    transcript: 'सुना गया',
    translation_ready: 'अनुवाद तैयार',
    translation_fallback: 'मूल टेक्स्ट दिखा रहे हैं',
    idle_title: 'सिस्टम शांत है',
    idle_sub: 'खपत पैटर्न की निगरानी हो रही है',
  },
  ta: {
    app_name: 'சூத்ரா கோ',
    decision: 'உள்ளூர் ஏஐ முடிவு',
    target: 'இலக்கு',
    confidence: 'நம்பிக்கை',
    savings: 'சேமிப்பு',
    deny: 'நிராகரி',
    approve: 'ஒப்புதல்',
    summary_title: 'சுருக்கம்',
    total_orders: 'ஆர்டர்கள்',
    total_savings: 'சேமிப்பு',
    top_supplier: 'சிறந்த வழங்குநர்',
    voice_hint: 'மைக் அழுத்தி பேசுங்கள்: "approve", "reject", "explain" — அல்லது ஒரு கேள்வி கேளுங்கள்.',
    local_voice: 'சாதனத்தின் குரல் இயந்திரம்',
    voice_footer: 'குரல் சாதனத்திலேயே இருக்கும். /voice/process பதிவேற்றம் இல்லை.',
    transcript: 'கேட்டது',
    translation_ready: 'மொழிபெயர்ப்பு தயார்',
    translation_fallback: 'அசல் உரை காட்டப்படுகிறது',
    idle_title: 'அமைப்பு தயார்',
    idle_sub: 'நுகர்வு முறை கண்காணிக்கப்படுகிறது',
  },
};

const speechLocales = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN' };
const sarvamLanguageCodes = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN' };

function isApproveCommand(text) {
  return /\b(approve|approved|yes|ok|okay|confirm|स्वीकृत|हाँ|ஒப்புதல்|சரி)\b/i.test(text);
}
function isRejectCommand(text) {
  return /\b(reject|rejected|deny|no|cancel|अस्वीकार|नहीं|நிராகரி|வேண்டாம்)\b/i.test(text);
}
function isExplainCommand(text) {
  return /\b(explain|why|reason|details|बताओ|क्यों|விளக்கு|ஏன்)\b/i.test(text);
}

export default function MobileApp() {
  const { isConnected, recommendation } = useSutraSocket();
  const [lang, setLang] = useState('en');
  const t = translations[lang];

  const [activeOrder, setActiveOrder] = useState(null);
  const [translatedOrder, setTranslatedOrder] = useState(null);
  const [summary, setSummary] = useState(DEMO_SUMMARY);
  const [voiceStatus, setVoiceStatus] = useState('idle');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastTranscript, setLastTranscript] = useState('');
  const [translationStatus, setTranslationStatus] = useState('idle');

  // Tracks which order is "current" so an in-flight translation for a
  // superseded order can't overwrite a newer one that arrived while we waited.
  const activeOrderIdRef = useRef(null);

  useEffect(() => {
    if (recommendation) setActiveOrder(recommendation);
  }, [recommendation]);

  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    const orderId = activeOrder?.po_number || activeOrder?.timestamp || null;
    activeOrderIdRef.current = orderId;
    translateActiveOrder(activeOrder, lang, orderId);
  }, [activeOrder, lang]);

  const fetchSummary = async () => {
    try {
      const res = await fetch(apiUrl('/analytics/summary'));
      setSummary(res.ok ? await res.json() : DEMO_SUMMARY);
    } catch (err) {
      console.error('Failed to fetch summary', err);
      setSummary(DEMO_SUMMARY);
    }
  };

  const cycleLanguage = () => {
    setLang((prev) => (prev === 'en' ? 'hi' : prev === 'hi' ? 'ta' : 'en'));
  };

  const translateText = async (text, targetLang) => {
    if (!text || targetLang === 'en') return text;

    const response = await fetch(translationUrl(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        source_language_code: 'en-IN',
        target_language_code: sarvamLanguageCodes[targetLang],
      }),
    });

    if (!response.ok) throw new Error(`Translation failed: ${response.status}`);

    const data = await response.json();
    return data.translated_text || data.translation || data.text || text;
    console.log(data);
    console.log(data.answer);
  };

  const translateActiveOrder = async (order, targetLang, orderId) => {
    if (!order) {
      setTranslatedOrder(null);
      setTranslationStatus('idle');
      return;
    }

    if (targetLang === 'en') {
      setTranslatedOrder(order);
      setTranslationStatus('idle');
      return;
    }

    setTranslationStatus('translating');

    try {
      const [recommendationText, reasoningText] = await Promise.all([
        translateText(order.recommendation || 'New procurement recommendation', targetLang),
        translateText(order.reasoning || 'Owner intervention required', targetLang),
      ]);

      // Bail if a newer order superseded this one while we were awaiting
      if (activeOrderIdRef.current !== orderId) return;

      setTranslatedOrder({ ...order, recommendation: recommendationText, reasoning: reasoningText });
      setTranslationStatus('translated');
    } catch (err) {
      console.warn('Translation unavailable, using original text:', err);
      if (activeOrderIdRef.current !== orderId) return;
      setTranslatedOrder(order);
      setTranslationStatus('fallback');
    }
  };

  const speak = (text) => {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speechLocales[lang];
    utterance.rate = 0.95;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  };

  const speakCurrentRecommendation = () => {
    const orderToRead = translatedOrder || activeOrder;
    if (!orderToRead) {
      speak('No pending recommendation right now.');
      return;
    }
    speak(`${orderToRead.recommendation}. ${orderToRead.reasoning}`);
  };

  const askQuestion = async (question) => {
    try {
      setVoiceStatus('thinking');
      const res = await fetch(apiUrl('/conversation/ask'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      const englishAnswer = data.answer || 'I could not find an answer.';

      const finalAnswer =
        lang === 'en' ? englishAnswer : await translateText(englishAnswer, lang);

      speak(finalAnswer);
      setVoiceStatus('answered');
    } catch (err) {
      console.error('Conversation request failed:', err);
      speak('Sorry, I could not reach the AI right now.');
      setVoiceStatus('error');
    }
  };

  const handleVoiceCommand = (text) => {
    if (!activeOrder) {
      speak('No pending order yet. Waiting for edge event.');
      return;
    }
    if (isApproveCommand(text)) return handleProcurementAction('approved');
    if (isRejectCommand(text)) return handleProcurementAction('rejected');
    if (isExplainCommand(text)) return speakCurrentRecommendation();

    // Anything else — treat it as a real question for Phi-3
    askQuestion(text);
  };

  const startRecording = async () => {
    try {
      const { speechRecognition } = await SpeechRecognition.checkPermissions();
      if (speechRecognition !== 'granted') {
        await SpeechRecognition.requestPermissions();
      }

      setVoiceStatus('listening');
      setIsRecording(true);
      setLastTranscript('');

      const result = await SpeechRecognition.start({
        language: speechLocales[lang],
        maxResults: 1,
        prompt: 'Awaiting SUTRA command',
        partialResults: false,
        popup: false,
      });

      if (result && result.matches && result.matches.length > 0) {
        const transcript = result.matches[0];
        setLastTranscript(transcript);
        setVoiceStatus('heard');
        handleVoiceCommand(transcript);
      }
    } catch (err) {
      console.error('Native speech engine terminated:', err);
      setVoiceStatus('no-input');
      speak('Sorry, I did not catch that. Please try again.');
    } finally {
      setIsRecording(false);
      setIsProcessing(false);
    }
  };

  const stopRecording = async () => {
    if (!isRecording) return;
    setIsProcessing(true);
    try {
      await SpeechRecognition.stop();
    } catch (err) {
      console.warn('Speech stop bypass:', err);
    }
  };

  const vibrateForAction = (status) => {
    if (!navigator.vibrate) return;
    navigator.vibrate(status === 'approved' ? [35, 35, 70] : [120, 40, 120]);
  };

  const handleProcurementAction = async (status) => {
    if (!activeOrder) return;

    vibrateForAction(status);

    const payload = {
      po_number: activeOrder.po_number || `PENDING-${Date.now()}`,
      action: status,
      item: activeOrder.item || activeOrder.event?.item || 'Rice',
      supplier: activeOrder.supplier,
      quantity: activeOrder.quantity || 30,
      savings: activeOrder.savings || 0,
      total_cost: activeOrder.total_cost || 1200,
      unit_price: activeOrder.total_cost && activeOrder.quantity
        ? parseFloat((activeOrder.total_cost / activeOrder.quantity).toFixed(2))
        : 40.0,
      expected_delivery_days: activeOrder.expected_delivery_days || 2,
      reasoning: activeOrder.reasoning || 'Owner intervention',
    };

    setActiveOrder(null);
    setTranslatedOrder(null);

    try {
      const endpoint = status === 'approved' ? '/procurement/approve' : '/procurement/reject';
      await fetch(apiUrl(endpoint), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      fetchSummary();
      speak(status === 'approved' ? 'Approved. Purchase order sent.' : 'Rejected. Purchase order stopped.');
    } catch (err) {
      console.error('Failed to dispatch action:', err);
      speak('Action failed. Please try again.');
    }
  };

  const displayOrder = translatedOrder || activeOrder;

  return (
    <div className="min-h-screen bg-slate-950 flex justify-center font-sans antialiased">
      <div className="w-full max-w-md bg-slate-900 flex flex-col h-[100dvh] shadow-2xl relative">
        {/* Header — compact, fixed */}
        <header className="flex-none bg-slate-950/80 backdrop-blur-md border-b border-slate-800 px-4 py-3 sticky top-0 z-10">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/50">
                <Zap className="w-3.5 h-3.5 text-white fill-white" />
              </div>
              <div>
                <h1 className="text-slate-200 font-bold text-sm tracking-wide leading-tight">{t.app_name}</h1>
                <div className="flex items-center gap-1.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                  <span className="text-[9px] font-medium text-slate-500 uppercase tracking-wider">
                    {isConnected ? 'Network Active' : 'Offline'}
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={cycleLanguage}
              className="flex items-center gap-1 text-[11px] font-bold text-slate-400 bg-slate-800/50 hover:bg-slate-700 px-2.5 py-1 rounded-full transition-colors uppercase border border-slate-700"
            >
              <Globe className="w-3 h-3" /> {lang}
            </button>
          </div>
        </header>

        {/* Main content — action card gets the majority of vertical space */}
        <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2 flex flex-col gap-3 custom-scrollbar min-h-0">
          {activeOrder ? (
            <div className="bg-slate-800 rounded-2xl border border-slate-700 p-4 shadow-lg overflow-hidden relative animate-in slide-in-from-top-4 fade-in duration-300 flex flex-col">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-500" />

              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-blue-400 fill-blue-400" />
                  <span className="text-[9px] font-bold text-blue-400 uppercase tracking-widest">{t.decision}</span>
                </div>
                <button
                  type="button"
                  onClick={speakCurrentRecommendation}
                  className="p-1.5 rounded-full bg-slate-900/70 hover:bg-slate-900 border border-slate-700 text-slate-300"
                  aria-label="Speak recommendation"
                >
                  <Volume2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <h3 className="text-slate-100 font-bold text-base leading-snug mb-2">{displayOrder?.recommendation}</h3>

              <div className="bg-slate-900/50 rounded-lg p-2.5 mb-2 border border-slate-800/50 max-h-20 overflow-y-auto">
                <p className="text-xs text-slate-400 italic leading-snug">"{displayOrder?.reasoning}"</p>
              </div>

              {lang !== 'en' && (
                <p className="text-[9px] text-slate-500 uppercase tracking-widest mb-2">
                  {translationStatus === 'translated' ? t.translation_ready : t.translation_fallback}
                </p>
              )}

              <div className="grid grid-cols-3 gap-2 text-sm mb-3">
                <div>
                  <div className="text-slate-500 text-[10px] mb-0.5">{t.target}</div>
                  <div className="text-slate-200 font-semibold text-xs truncate">{activeOrder.supplier}</div>
                </div>
                <div>
                  <div className="text-slate-500 text-[10px] mb-0.5">{t.savings}</div>
                  <div className="text-emerald-400 font-bold text-xs">₹{activeOrder.savings}</div>
                </div>
                <div>
                  <div className="text-slate-500 text-[10px] mb-0.5">{t.confidence}</div>
                  <div className="text-blue-400 font-bold text-xs">{activeOrder.confidence || 95}%</div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleProcurementAction('rejected')}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-950 text-slate-300 font-bold text-xs border border-slate-700 transition-colors"
                >
                  <XCircle className="w-3.5 h-3.5" /> {t.deny}
                </button>
                <button
                  onClick={() => handleProcurementAction('approved')}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md transition-colors"
                >
                  <ShieldCheck className="w-3.5 h-3.5" /> {t.approve}
                </button>
              </div>
            </div>
          ) : (
            <div className="py-8 flex flex-col items-center justify-center text-center bg-slate-800/40 rounded-2xl border border-slate-800 border-dashed">
              <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-3">
                <ShieldCheck className="w-5 h-5 text-slate-600" />
              </div>
              <h4 className="text-sm font-bold text-slate-300">{t.idle_title}</h4>
              <p className="text-xs text-slate-500 mt-1">{t.idle_sub}</p>
            </div>
          )}

          {/* Compact summary strip */}
          <div className="flex-none bg-slate-800/50 rounded-xl border border-slate-700/50 px-4 py-3">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              <h3 className="text-slate-300 font-semibold text-xs uppercase tracking-wide">{t.summary_title}</h3>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-slate-200 font-bold text-sm">{summary?.total_orders ?? 0}</div>
                <div className="text-slate-500 text-[10px] uppercase">{t.total_orders}</div>
              </div>
              <div>
                <div className="text-emerald-400 font-bold text-sm">₹{summary?.total_savings ?? 0}</div>
                <div className="text-slate-500 text-[10px] uppercase">{t.total_savings}</div>
              </div>
              <div>
                <div className="text-slate-200 font-bold text-sm truncate">{summary?.best_supplier ?? '—'}</div>
                <div className="text-slate-500 text-[10px] uppercase">{t.top_supplier}</div>
              </div>
            </div>
          </div>

          {/* Compact voice status strip */}
          <div className="flex-none rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3 text-slate-300 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Mic className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-semibold">{t.local_voice}</span>
              </div>
              <span className="text-slate-500 uppercase tracking-wide flex items-center gap-1">
                {voiceStatus}
                {isProcessing ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
              </span>
            </div>
            {lastTranscript && (
              <p className="mt-1.5 text-slate-500">
                {t.transcript}: <span className="text-slate-300">"{lastTranscript}"</span>
              </p>
            )}
          </div>
        </div>

        {/* Mic button — fixed footer */}
        <div className="flex-none px-6 py-4 bg-slate-900 border-t border-slate-800 flex flex-col items-center justify-center">
          <button
            type="button"
            onPointerDown={startRecording}
            onPointerUp={stopRecording}
            onPointerLeave={stopRecording}
            disabled={isProcessing}
            className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all ${
              isRecording
                ? 'bg-red-500 scale-110 shadow-red-500/40'
                : isProcessing
                  ? 'bg-slate-800 border border-slate-700 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-500 hover:scale-105 shadow-blue-900/50'
            }`}
          >
            {isProcessing ? (
              <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
            ) : (
              <Mic className={`w-5 h-5 ${isRecording ? 'text-white animate-pulse' : 'text-white'}`} />
            )}
          </button>

          <p className="text-[10px] text-slate-500 mt-2 text-center max-w-xs">{t.voice_hint}</p>

          <div className="text-center mt-2 flex items-center justify-center gap-1.5 opacity-50">
            <Lock className="w-3 h-3 text-slate-500" />
            <span className="text-[9px] text-slate-500 uppercase tracking-widest font-semibold">
              {t.voice_footer}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}