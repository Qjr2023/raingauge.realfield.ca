import Modal from './Modal';
import RainChart from './RainChart';

/**
 * The chart behind one of the three point values: the API's summary line, then the kit chart
 * (which carries its own heading and caption).
 */
function RainChartModal({ visible, onClose, title, summary, kind, rain, stats }) {
  return (
    <Modal visible={visible} onClose={onClose} title={title} wide>
      {summary && <p className="chart-summary">{summary}</p>}
      <RainChart kind={kind} rain={rain} stats={stats} />
      <button type="button" className="btn-close" onClick={onClose}>
        Close
      </button>
    </Modal>
  );
}

export default RainChartModal;
