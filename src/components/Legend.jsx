/**
 * Legend of the selected overlay: title, colour bar and range, from /legend_info
 * (fetched once in HomePage via useLegendInfo).
 */
function Legend({ selectedLayer, legendInfo, loading }) {
  if (loading) {
    return (
      <div className="legend">
        <div className="spinner" />
      </div>
    );
  }

  const layer = legendInfo?.[selectedLayer];
  if (!layer) return null;

  return (
    <div className="legend">
      <div className="legend-title">{layer.title}</div>
      <img className="legend-bar" src={layer.uri} alt="Color scale" />
      <div className="legend-range">
        <span>{layer.min}</span>
        <span>{layer.max}</span>
      </div>
    </div>
  );
}

export default Legend;
