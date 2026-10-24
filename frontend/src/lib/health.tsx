import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, errorMessage } from '../api/client';
import type { HealthResult } from '../api/types';

interface HealthState {
  health: HealthResult | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const HealthContext = createContext<HealthState>({
  health: null,
  loading: true,
  error: null,
  refresh: async () => {},
});

export function HealthProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<HealthResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.health();
      setHealth(response.result);
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(), 60_000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  const value = useMemo(
    () => ({ health, loading, error, refresh }),
    [health, loading, error, refresh],
  );

  return <HealthContext.Provider value={value}>{children}</HealthContext.Provider>;
}

export function useHealth(): HealthState {
  return useContext(HealthContext);
}
