import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { outlineLayer } from '../kit/index.js';

// The kit calls Leaflet through the global L; the bundled Leaflet sets it, this keeps it explicit.
if (typeof window !== 'undefined' && !window.L) window.L = L;

// Prairie Layers' style for the cropland extent
const STYLE = { color: '#ffd84a', weight: 2, opacity: 1, fill: false };
const WEIGHT_BY_ZOOM = { 5: 1.5, 7: 2, 9: 2.5 };

/**
 * Cropland outline (rendered inside MapContainer): the GeoJSON at url drawn on top of the rain
 * overlay in the Prairie Layers style, line weight growing with zoom.
 */
function CroplandOutline({ url }) {
  const map = useMap();
  useEffect(() => {
    if (!url) return undefined;
    const lyr = outlineLayer(url, { map, style: STYLE, weightByZoom: WEIGHT_BY_ZOOM });
    lyr.addTo(map);
    return () => {
      lyr.remove();
    };
  }, [map, url]);
  return null;
}

export default CroplandOutline;
