import { useEffect, useRef, useState } from 'react';
import MapView from '../components/MapView';
import ValuesModal from '../components/ValuesModal';
import InfoModal from '../components/InfoModal';
import Legend from '../components/Legend';
import ButtonBar from '../components/ButtonBar';
import LogoCarousel from '../components/LogoCarousel';
import { TapIcon } from '../components/Icons';
import RainChartModal from '../components/RainChartModal';
import { fetchPrecipitationValues } from '../utils/mapPress';
import { loadRainSeries } from '../utils/rainSeries';
import { useLegendInfo } from '../hooks/useLegendInfo';
import { useRainStats } from '../hooks/useRainStats';
import { withRange } from '../utils/tiles';

function HomePage() {
  const [selectedLayer, setSelectedLayer] = useState('weeklyRain');
  const [overlayOpacity, setOverlayOpacity] = useState(0.8);
  const [showRoads, setShowRoads] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [infoModalVisible, setInfoModalVisible] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [activeChart, setActiveChart] = useState(null); // 'daily' | 'season' | 'year'
  const [modalData, setModalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [markerPosition, setMarkerPosition] = useState(null);
  const [hasInteracted, setHasInteracted] = useState(false);
  // The daily rain record at the tapped point, for the charts: { loading, data | null, error | null }
  const [rain, setRain] = useState({ loading: false, data: null, error: null });
  // The latest tap wins: results of an earlier tap are dropped when they arrive
  const tapSeq = useRef(0);
  // Auto-stretch (always on): the colour ramp spans the pixels on screen (range from AutoStretch)
  // instead of the region-wide rescale in the API's template.
  const [range, setRange] = useState(null);
  const legend = useLegendInfo();
  const rainStats = useRainStats();
  // Tile URL template and legend of the selected overlay; the API builds the template with the day's colormap.
  const layer = legend.info?.[selectedLayer];
  const overlayUrl = layer ? withRange(layer.tiles, range) : undefined;

  // A new layer starts from its own region-wide range until its on-screen range arrives
  useEffect(() => {
    setRange(null);
  }, [selectedLayer]);

  const handleMapPress = async (latlng) => {
    const seq = ++tapSeq.current;
    setHasInteracted(true);
    setMarkerPosition(latlng);
    setModalData(null);
    setLoading(true);
    setModalVisible(true);
    // The charts' series is read alongside the totals so it is ready when a chart is opened
    const pointTemplate = layer?.point;
    const stats = rainStats.stats;
    if (!pointTemplate || !stats) {
      setRain({
        loading: false,
        data: null,
        error: 'The chart data is not available yet. Please tap the map again.',
      });
    } else {
      setRain({ loading: true, data: null, error: null });
      loadRainSeries({ pointTemplate, stats, latlng }).then(
        (data) => {
          if (seq !== tapSeq.current) return;
          if (data.fetchedYears.length === 0) {
            setRain({
              loading: false,
              data: null,
              error:
                'Could not load the rain record. Please check your connection and tap the map again.',
            });
          } else {
            setRain({ loading: false, data, error: null });
          }
        },
        (e) => {
          console.error('Error loading the rain series:', e);
          if (seq === tapSeq.current)
            setRain({ loading: false, data: null, error: 'Could not load the rain record.' });
        }
      );
    }
    const data = await fetchPrecipitationValues(latlng);
    if (seq !== tapSeq.current) return;
    setModalData(data);
    setLoading(false);
  };

  const openChart = (chart) => {
    setModalVisible(false);
    setActiveChart(chart);
  };

  const closeChart = () => {
    setActiveChart(null);
    setModalVisible(true);
  };

  return (
    <div className="home">
      <div className="map-area">
        <MapView
          selectedLayer={selectedLayer}
          layer={layer}
          overlayUrl={overlayUrl}
          onRange={setRange}
          overlayOpacity={overlayOpacity}
          showRoads={showRoads}
          showLabels={showLabels}
          onMapPress={handleMapPress}
          markerPosition={markerPosition}
        />
        <Legend
          layer={layer}
          range={range}
          loading={legend.loading && !layer}
          error={legend.error}
          onRetry={legend.reload}
        />
        {!hasInteracted && (
          <div className="map-hint" role="status">
            <TapIcon size={16} />
            <span>Tap anywhere on the map to get precipitation</span>
          </div>
        )}
      </div>

      <ValuesModal
        visible={modalVisible}
        loading={loading}
        modalData={modalData}
        onClose={() => setModalVisible(false)}
        onDailyChartOpen={() => openChart('daily')}
        onSeasonChartOpen={() => openChart('season')}
        onYearChartOpen={() => openChart('year')}
      />

      <RainChartModal
        visible={activeChart === 'daily'}
        onClose={closeChart}
        title="Daily rain, last 30 days"
        summary={modalData?.weekly_precipitation}
        kind="daily"
        rain={rain}
        stats={rainStats.stats}
      />

      <RainChartModal
        visible={activeChart === 'season'}
        onClose={closeChart}
        title="Growing season vs earlier years"
        summary={modalData?.seasonal_precipitation}
        kind="season"
        rain={rain}
        stats={rainStats.stats}
      />

      <RainChartModal
        visible={activeChart === 'year'}
        onClose={closeChart}
        title="Crop year vs earlier years"
        summary={modalData?.yearly_precipitation}
        kind="year"
        rain={rain}
        stats={rainStats.stats}
      />

      <InfoModal
        visible={infoModalVisible}
        onClose={() => setInfoModalVisible(false)}
      />

      <ButtonBar
        selectedLayer={selectedLayer}
        overlayOpacity={overlayOpacity}
        onOverlayOpacityChange={setOverlayOpacity}
        showRoads={showRoads}
        showLabels={showLabels}
        onShowRoadsChange={setShowRoads}
        onShowLabelsChange={setShowLabels}
        onInfoPress={() => setInfoModalVisible(true)}
        onLayerChange={setSelectedLayer}
        legendInfo={legend.info}
      />

      <div className="footer-logo">
        <LogoCarousel />
      </div>
    </div>
  );
}

export default HomePage;
