import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import AutoStretch from './AutoStretch';
import CroplandOutline from './CroplandOutline';

const PIN_ICON = L.divIcon({
  className: 'map-pin',
  html:
    '<svg viewBox="0 0 28 38" width="28" height="38" aria-hidden="true">' +
    '<path d="M14 1.5C7.1 1.5 1.5 7 1.5 13.8 1.5 23 14 36.5 14 36.5S26.5 23 26.5 13.8C26.5 7 20.9 1.5 14 1.5z" ' +
    'fill="#0b6a41" stroke="#fff" stroke-width="2"/>' +
    '<circle cx="14" cy="14" r="4.5" fill="#fff"/></svg>',
  iconSize: [28, 38],
  iconAnchor: [14, 37],
});

const CENTER = [52.1557, -106.69];
// Rain tiles exist up to zoom 10 (the data is 2.5 km per pixel); Leaflet scales them up beyond that.
const RAIN_MAX_NATIVE_ZOOM = 10;

const REFERENCE_LAYERS = {
  roads:
    'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
  labels:
    'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
};

function MapClickHandler({ onMapPress }) {
  useMapEvents({
    click(e) {
      onMapPress({
        latitude: e.latlng.lat,
        longitude: e.latlng.lng,
      });
    },
  });
  return null;
}

function InvalidateSize() {
  const map = useMap();
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 100);
    return () => clearTimeout(t);
  }, [map]);
  return null;
}

// layer: the selected legend_info entry (tiles template, stats URL, outline URL); overlayUrl: its
// tiles template with the auto-stretch range applied (auto-stretch is always on). The rain
// TileLayer is keyed on the layer name, so a new range only calls setUrl (a repaint, no remount).
function MapView({
  selectedLayer,
  layer,
  overlayUrl,
  onRange,
  overlayOpacity = 0.8,
  showRoads = true,
  showLabels = true,
  onMapPress,
  markerPosition,
}) {
  return (
    <MapContainer
      center={CENTER}
      zoom={7}
      className="map-container"
      zoomControl
      attributionControl={false}
    >
      <InvalidateSize />
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        maxZoom={15}
      />
      {overlayUrl && (
        <TileLayer
          key={selectedLayer}
          url={overlayUrl}
          opacity={overlayOpacity}
          maxZoom={15}
          maxNativeZoom={RAIN_MAX_NATIVE_ZOOM}
        />
      )}
      {layer?.outline && <CroplandOutline url={layer.outline} />}
      <AutoStretch layer={layer ?? null} onRange={onRange} />
      {showRoads && (
        <TileLayer url={REFERENCE_LAYERS.roads} maxZoom={15} />
      )}
      {showLabels && (
        <TileLayer url={REFERENCE_LAYERS.labels} maxZoom={15} />
      )}
      <MapClickHandler onMapPress={onMapPress} />
      {markerPosition && (
        <Marker
          position={[markerPosition.latitude, markerPosition.longitude]}
          icon={PIN_ICON}
        />
      )}
    </MapContainer>
  );
}

export default MapView;
