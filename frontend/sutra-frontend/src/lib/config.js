const DEFAULT_BACKEND_PORT = import.meta.env.VITE_SUTRA_BACKEND_PORT || '8000';

function normalizeBaseUrl(url) {
  return url?.replace(/\/+$/, '');
}

function detectApiBaseUrl() {
  const configuredUrl = normalizeBaseUrl(import.meta.env.VITE_SUTRA_API_BASE_URL);

  if (configuredUrl) {
    return configuredUrl;
  }

  if (typeof window !== 'undefined') {
    const { hostname } = window.location;

    if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return `http://${hostname}:${DEFAULT_BACKEND_PORT}`;
    }
  }

  return `http://localhost:${DEFAULT_BACKEND_PORT}`;
}

export const API_BASE_URL = detectApiBaseUrl();
export const TRANSLATION_PATH = import.meta.env.VITE_SUTRA_TRANSLATION_PATH || '/translation/translate';

export const WS_BASE_URL = API_BASE_URL.replace(/^http/i, 'ws');

export const DEMO_SUMMARY = {
  total_orders: 0,
  total_savings: 0,
  best_supplier: '—',
};

export function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export function wsUrl(path) {
  return `${WS_BASE_URL}${path}`;
}

export function translationUrl() {
  return `${API_BASE_URL}${TRANSLATION_PATH}`;
}
