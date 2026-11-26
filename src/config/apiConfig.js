const API_CONFIG = {
  // Build-time override (VITE_API_BASE_URL). A self-hosted build sets the same-origin path that
  // nginx proxies to the API in server/ (see deploy/).
  BASE_URL:
    import.meta.env.VITE_API_BASE_URL || 'https://api-2vudqtm7bq-uc.a.run.app',
  // BASE_URL: 'https://api.realfield.ca',
  // BASE_URL: 'http://localhost:8000',
  ENDPOINTS: {
    PRECIPITATION_VALUES: '/precipitation_values',
    DAILY_PRECIPITATION: '/daily_precipitation',
    SEASON_COMPARISON: '/season_comparison',
    YEAR_COMPARISON: '/year_comparison',
    VERSION: '/version',
    LEGEND_INFO: '/legend_info',
  },
};

export default API_CONFIG;
