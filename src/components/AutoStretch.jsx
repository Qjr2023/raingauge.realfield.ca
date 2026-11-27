import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import { createDra } from '../kit/index.js';

/**
 * Auto-stretch (rendered inside MapContainer): after each map move the kit's controller asks the
 * API for the 2nd..98th percentile of the selected layer's pixels on screen and reports the range
 * through onRange (null when off). The controller is created once; its callbacks read the current
 * layer from a ref, so a layer change only needs a refresh.
 */
function AutoStretch({ layer, enabled, onRange }) {
  const map = useMap();
  const layerRef = useRef(layer);
  const onRangeRef = useRef(onRange);
  const draRef = useRef(null);
  layerRef.current = layer;
  onRangeRef.current = onRange;

  useEffect(() => {
    const dra = createDra({
      map,
      statsUrl: () => layerRef.current?.stats ?? null,
      bounds: () => map.getBounds(),
      fadeLow: () => !!layerRef.current?.fade_low,
      onRange: (range) => onRangeRef.current(range),
    });
    draRef.current = dra;
    return () => {
      dra.destroy();
      draRef.current = null;
    };
  }, [map]);

  useEffect(() => {
    draRef.current?.setEnabled(enabled);
  }, [enabled]);

  useEffect(() => {
    if (!layer) onRangeRef.current(null);
    else if (draRef.current?.enabled) draRef.current.refresh();
  }, [layer]);

  return null;
}

export default AutoStretch;
