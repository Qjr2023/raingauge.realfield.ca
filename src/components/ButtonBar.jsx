import { useState } from 'react';
import AppButton from './AppButton';
import Modal from './Modal';
import { CheckIcon, InfoIcon, LayersIcon } from './Icons';

const LAYERS = [
  { value: 'weeklyRain', label: 'Last week' },
  { value: 'seasonRain', label: 'Growing Season' },
  { value: 'yearRain', label: 'Crop Year' },
];

// Swatch beside each option: the layer's ramp from legend_info, blank until it has loaded.
const swatchFor = (info) =>
  info?.palette
    ? `linear-gradient(135deg, ${info.palette.join(', ')})`
    : 'transparent';

function ButtonBar({
  selectedLayer,
  overlayOpacity,
  onOverlayOpacityChange,
  showRoads,
  showLabels,
  onShowRoadsChange,
  onShowLabelsChange,
  onInfoPress,
  onLayerChange,
  legendInfo,
}) {
  const [layerModalVisible, setLayerModalVisible] = useState(false);

  const current = LAYERS.find((l) => l.value === selectedLayer);

  const handleLayerChange = (value) => {
    onLayerChange(value);
    setLayerModalVisible(false);
  };

  return (
    <div className="button-bar">
      <AppButton
        theme="primary"
        label="Select Layer"
        sublabel={current ? current.label : undefined}
        icon={<LayersIcon />}
        onPress={() => setLayerModalVisible(true)}
      />
      <AppButton
        label="Instruction and info"
        icon={<InfoIcon />}
        onPress={onInfoPress}
      />

      <Modal
        visible={layerModalVisible}
        onClose={() => setLayerModalVisible(false)}
        title="Select Layer"
      >
        {LAYERS.map((layer) => {
          const active = layer.value === selectedLayer;
          return (
            <button
              key={layer.value}
              type="button"
              className={
                active ? 'layer-option layer-option--active' : 'layer-option'
              }
              aria-pressed={active}
              onClick={() => handleLayerChange(layer.value)}
            >
              <span
                className="layer-swatch"
                style={{ background: swatchFor(legendInfo?.[layer.value]) }}
                aria-hidden="true"
              />
              <span className="layer-option__label">{layer.label}</span>
              {active && <CheckIcon size={18} />}
            </button>
          );
        })}
        <div className="map-layer-toggles">
          <label className="map-layer-toggle">
            <input
              type="checkbox"
              checked={showRoads}
              onChange={(e) => onShowRoadsChange(e.target.checked)}
            />
            <span>Show roads</span>
          </label>
          <label className="map-layer-toggle">
            <input
              type="checkbox"
              checked={showLabels}
              onChange={(e) => onShowLabelsChange(e.target.checked)}
            />
            <span>Show place names</span>
          </label>
        </div>
        <label className="opacity-control" htmlFor="overlay-opacity">
          <span className="opacity-control__label">Overlay transparency</span>
          <div className="opacity-control__row">
            <input
              id="overlay-opacity"
              type="range"
              min={0}
              max={100}
              value={Math.round(overlayOpacity * 100)}
              onChange={(e) =>
                onOverlayOpacityChange(Number(e.target.value) / 100)
              }
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(overlayOpacity * 100)}
            />
            <span className="opacity-control__value">
              {Math.round(overlayOpacity * 100)}%
            </span>
          </div>
        </label>
        <button
          type="button"
          className="btn-close"
          onClick={() => setLayerModalVisible(false)}
        >
          Close
        </button>
      </Modal>
    </div>
  );
}

export default ButtonBar;
