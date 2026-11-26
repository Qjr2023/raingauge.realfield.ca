import { useEffect, useState } from 'react';
import API_CONFIG from '../config/apiConfig';

/**
 * Fetches /legend_info once: titles, breaks, palette, legend image and the tile URL template of
 * each overlay. The map and the legend both read it, so they always agree.
 */
export function useLegendInfo() {
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch(
          `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.LEGEND_INFO}`
        );
        const data = await response.json();
        if (!cancelled) setInfo(data);
      } catch (error) {
        console.error('Error fetching legend:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { info, loading };
}
