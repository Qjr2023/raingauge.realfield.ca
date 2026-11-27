import { fmtRange } from '../utils/tiles';

/**
 * Legend of the selected overlay: label, colour bar and range, from the matching /legend_info
 * entry (fetched in HomePage via useLegendInfo). The ends show the on-screen range (range, from
 * AutoStretch) once it has arrived, else the layer's region-wide range. Shows a spinner until the
 * first load and a retry prompt when the load failed and there is nothing to show yet.
 */

// The gradient bar is drawn in CSS from the palette. An older API without palette/range/label
// falls back to the legend PNG and the min/max text.
const hasRamp = (layer) =>
  Array.isArray(layer.palette) &&
  layer.palette.length > 1 &&
  Array.isArray(layer.range) &&
  typeof layer.label === 'string';

function Legend({ layer, range, loading, error, onRetry }) {
  if (loading) {
    return (
      <div className="legend">
        <div className="spinner" />
      </div>
    );
  }

  if (error && !layer) {
    return (
      <div className="legend" role="status">
        Rain layers unavailable.{' '}
        <button type="button" className="btn-text" onClick={onRetry}>
          Retry
        </button>
      </div>
    );
  }

  if (!layer) return null;

  if (!hasRamp(layer)) {
    return (
      <div className="legend" role="group" aria-label="Map legend">
        <div className="legend-title">{layer.title}</div>
        <img
          className="legend-bar"
          src={layer.uri}
          alt={`${layer.title}: colour scale from ${layer.min} to ${layer.max}`}
        />
        <div className="legend-range">
          <span>{layer.min}</span>
          <span>{layer.max}</span>
        </div>
      </div>
    );
  }

  // The on-screen range once auto-stretch has one, else the region-wide range. With fade_low the
  // low end is 0 (the bottom of the ramp fades out) unless the stretch starts above it.
  const lo = range && range[0] > 0 ? fmtRange(range[0]) : 0;
  const hi = fmtRange(range ? range[1] : layer.range[1]);
  return (
    <div className="legend" role="group" aria-label="Map legend">
      <div className="legend-title">
        {layer.label} <span className="legend-units">{layer.units}</span>
      </div>
      <div
        className="legend-bar"
        style={{ background: `linear-gradient(90deg, ${layer.palette.join(', ')})` }}
        role="img"
        aria-label={`${layer.label}: colour scale from ${lo} to ${hi} ${layer.units} and above`}
      />
      <div className="legend-range">
        <span>{lo}</span>
        <span>≥ {hi}</span>
      </div>
    </div>
  );
}

export default Legend;
