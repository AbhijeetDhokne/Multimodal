export type AIProvider = 'gemini' | 'openai' | 'auto';

const KEY_STORAGE = 'constructiq_ai_key';
const PROVIDER_STORAGE = 'constructiq_ai_provider';

export interface ApiKeyState {
  apiKey: string;
  provider: AIProvider;
}

export const apiKeyStore: ApiKeyState = {
  apiKey: localStorage.getItem(KEY_STORAGE) || '',
  provider: (localStorage.getItem(PROVIDER_STORAGE) as AIProvider) || 'auto',
};

export function setApiKey(key: string, provider: AIProvider = 'auto') {
  apiKeyStore.apiKey = key.trim();
  apiKeyStore.provider = provider;
  localStorage.setItem(KEY_STORAGE, key.trim());
  localStorage.setItem(PROVIDER_STORAGE, provider);
}

export function clearApiKey() {
  apiKeyStore.apiKey = '';
  apiKeyStore.provider = 'auto';
  localStorage.removeItem(KEY_STORAGE);
  localStorage.removeItem(PROVIDER_STORAGE);
}
