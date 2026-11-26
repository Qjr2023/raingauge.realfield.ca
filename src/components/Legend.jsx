/**
 * Legend of the selected overlay: title, colour bar and range, from the matching /legend_info
 * entry (fetched in HomePage via useLegendInfo). Shows a spinner until the first load and a
 * retry prompt when the load failed and there is nothing to show yet.
 */
function Legend({ layer, loading, error, onRetry }) {
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

export default Legend;
