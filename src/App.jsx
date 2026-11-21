import HomePage from './pages/HomePage';
import UpdateBanner from './components/UpdateBanner';
import InstallPrompt from './components/InstallPrompt';
import { DropIcon } from './components/Icons';
import API_CONFIG from './config/apiConfig';

function App() {
  return (
    <>
      <UpdateBanner
        remoteUrl={`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.VERSION}`}
      />
      <header className="app-header">
        <span className="app-header-icon">
          <DropIcon size={26} />
        </span>
        <h1>Virtual Rain Gauge</h1>
      </header>
      <HomePage />
      <InstallPrompt />
    </>
  );
}

export default App;
