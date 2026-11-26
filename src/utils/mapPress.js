import axios from 'axios';
import API_CONFIG from '../config/apiConfig';

export async function fetchPrecipitationValues({ latitude, longitude }) {
  try {
    const response = await axios.post(
      `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PRECIPITATION_VALUES}`,
      { lat: latitude, lon: longitude }
    );
    return response.data;
  } catch (error) {
    console.error(error);
    // The API explains a 404 or 503 in `detail`; the modal shows it instead of the generic text.
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return { error: detail };
    return null;
  }
}
