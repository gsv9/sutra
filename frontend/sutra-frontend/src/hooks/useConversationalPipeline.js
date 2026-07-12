import { useState } from 'react';
import { apiUrl, translationUrl } from '../lib/config';

const speechLocales = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN' };
const sarvamLanguageCodes = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN' };

export function useConversationalPipeline(lang) {
  const [voiceStatus, setVoiceStatus] = useState('idle');
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastTranscript, setLastTranscript] = useState('');
  const [translationStatus, setTranslationStatus] = useState('idle');
  const [aiResponse, setAiResponse] = useState('');

  const translateText = async (text, targetLang, sourceLang = 'en') => {
    if (!text || targetLang === sourceLang) return text;
    const response = await fetch(translationUrl(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        source_language_code: sarvamLanguageCodes[sourceLang],
        target_language_code: sarvamLanguageCodes[targetLang],
      }),
    });
    if (!response.ok) throw new Error('Translation failed');
    const data = await response.json();
    return data.translated_text || data.translation || data.text || text;
  };

  const translateActiveOrder = async (order, targetLang) => {
    if (!order) {
      setTranslationStatus('idle');
      return null;
    }
    if (targetLang === 'en') {
      setTranslationStatus('idle');
      return order;
    }

    setTranslationStatus('translating');
    try {
      const [recText, resText] = await Promise.all([
        translateText(order.recommendation, targetLang),
        translateText(order.reasoning, targetLang),
      ]);
      setTranslationStatus('translated');
      return { ...order, recommendation: recText, reasoning: resText };
    } catch (err) {
      setTranslationStatus('fallback');
      return order;
    }
  };

  const speak = (text) => {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speechLocales[lang];
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  };

  const askPhi3 = async (transcript) => {
    setIsProcessing(true);
    setAiResponse('');
    try {
      setVoiceStatus('Translating to English...');
      const englishQuestion = await translateText(transcript, 'en', lang);
      
      setVoiceStatus('Phi-3 Reasoning...');
      const res = await fetch(apiUrl('/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: englishQuestion }),
      });
      const data = await res.json();
      
      setVoiceStatus('Translating response...');
      const localizedAnswer = await translateText(data.answer, lang, 'en');
      
      setAiResponse(localizedAnswer);
      speak(localizedAnswer);
      setVoiceStatus('idle');
    } catch (err) {
      console.error('Pipeline error:', err);
      const errorMsg = lang === 'en' ? 'Connection failed.' : 'नेटवर्क त्रुटि';
      setAiResponse(errorMsg);
      speak(errorMsg);
      setVoiceStatus('error');
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    voiceStatus, setVoiceStatus,
    isProcessing, setIsProcessing,
    lastTranscript, setLastTranscript,
    translationStatus,
    aiResponse, setAiResponse,
    translateActiveOrder, speak, askPhi3
  };
}