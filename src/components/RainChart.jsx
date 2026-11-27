import { useEffect, useMemo, useRef, useState } from 'react';
import {
  dailyData,
  compareData,
  dailyChart,
  compareChart,
  bindReadout,
} from '../kit/index.js';
import '../kit/rain-charts.css';

// One colour per earlier year, oldest first: readable on the white sheet (the kit's pastel set is
// for Prairie Layers' green card).
const APP_YEAR_COLORS = [
  '#1f77b4',
  '#e07b00',
  '#2a9d3a',
  '#8e5bc5',
  '#d62728',
  '#0f9bb0',
];

/**
 * One of the kit's rain charts at the tapped point. kind: 'daily' (30 days of bars), 'season' or
 * 'year' (the cumulative window against earlier years). rain: { loading, data, error } from the
 * page; stats: /rain_stats. The kit draws inline SVG as a string and binds the readout itself, so
 * the chart lives in a container React leaves alone.
 */
function RainChart({ kind, rain, stats }) {
  const el = useRef(null);
  const [hotYear, setHotYear] = useState(null);
  const data = rain.data;
  const ready = Boolean(data && stats && data.any);

  // the numbers the chart draws from (null for a comparison with no year to show)
  const chart = useMemo(() => {
    if (!ready) return null;
    return kind === 'daily'
      ? dailyData(data.series, stats)
      : compareData(data.series, stats, kind, data.fetchedYears);
  }, [ready, data, stats, kind]);

  useEffect(() => {
    const node = el.current;
    if (!chart || !node) return undefined;
    if (kind === 'daily') {
      node.innerHTML = dailyChart(chart, { zoom: false });
      bindReadout(node.querySelector('.chart'), chart, 'daily');
    } else {
      node.innerHTML = compareChart(chart, kind, {
        hotYear,
        yearColors: APP_YEAR_COLORS,
        zoom: false,
      });
      bindReadout(node.querySelector('.chart'), chart, 'compare', {
        onHotYear: setHotYear,
      });
    }
    return () => {
      node.innerHTML = '';
    };
  }, [chart, kind, hotYear]);

  if (rain.loading) return <div className="spinner" />;
  if (rain.error) {
    return (
      <div className="error-box">
        <p>{rain.error}</p>
      </div>
    );
  }
  if (!data || !stats) return null;
  if (!data.any) {
    return <p className="chart-empty">No data at this location</p>;
  }
  if (!chart) {
    return (
      <p className="chart-empty">
        Earlier years appear once the history is loaded.
      </p>
    );
  }
  return <div className="rain-charts rain-charts--app" ref={el} />;
}

export default RainChart;
