import { useEffect, useState } from 'react';
import API_CONFIG from '../config/apiConfig';

/**
 * /legend_info: titles, breaks, palette, legend image and the tile URL template of each overlay.
 * Fetched on mount, on retry, and again when the tab comes back to the foreground (the colormap
 * in the tile URL changes with each day's data). The map and the legend both read it.
 * The previous info is kept while a refetch is in flight, so the overlay stays on the map.
 */
export function useLegendInfo() {
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const response = await fetch(
          `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.LEGEND_INFO}`
        );
        if (!response.ok) throw new Error(`legend_info ${response.status}`);
        const data = await response.json();
        if (!cancelled) setInfo(data);
      } catch (e) {
        console.error('Error fetching legend_info:', e);
        if (!cancelled) setError(e);
      } finally {
        if (!cancelled) setLoading(false);
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

  return { info, loading, error, reload: () => setAttempt((n) => n + 1) };
}
