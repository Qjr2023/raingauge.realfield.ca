import { useEffect, useState } from 'react';
import API_CONFIG from '../config/apiConfig';

/**
 * /rain_stats: the newest day, the crop years on the server and the start and end of each window
 * (week, season, crop year). The charts draw from it. Fetched on mount and again when the tab comes
 * back to the foreground (the windows move with each day's data); the previous stats are kept while
 * a refetch is in flight.
 */
export function useRainStats() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    (async () => {
      try {
        const response = await fetch(
          `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.RAIN_STATS}`
        );
        if (!response.ok) throw new Error(`rain_stats ${response.status}`);
        const data = await response.json();
        if (!cancelled) setStats(data);
      } catch (e) {
        console.error('Error fetching rain_stats:', e);
        if (!cancelled) setError(e);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === 'visible') setAttempt((n) => n + 1);
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => document.removeEventListener('visibilitychange', onVisible);
  }, []);

  return { stats, error };
}
