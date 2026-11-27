import { fetchRainSeries } from '../kit/index.js';

// How many crop-year stacks to read at a tapped point: up to seven earlier years for the comparison
// charts, plus one because a growing season straddles two crop years (as Prairie Layers does).
const STACKS = 8;

/**
 * The daily rain record at a point, read straight from TiTiler through the API's point route
 * (one request per crop-year stack; the template holds {cy}, {lon} and {lat}).
 * Returns the kit's { series, fetchedYears, any }.
 */
export async function loadRainSeries({ pointTemplate, stats, latlng }) {
  const lon = latlng.longitude.toFixed(5);
  const lat = latlng.latitude.toFixed(5);
  const pointUrl = (cy) =>
    pointTemplate
      .replace('{cy}', cy)
      .replace('{lon}', lon)
      .replace('{lat}', lat);
  return fetchRainSeries({
    pointUrl,
    cropYears: stats.crop_years.slice(-STACKS),
    lat: latlng.latitude,
    lng: latlng.longitude,
  });
}
