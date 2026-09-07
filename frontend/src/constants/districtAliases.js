/**
 * Land Acquisition Delay Predictor - District Name Aliases for GeoJSON Polygon Matching
 * 
 * Maps post-2011 newly bifurcated or renamed Indian districts to their
 * corresponding parent/historical district polygon in the 2011 Census GeoJSON (dists11.geojson).
 */

export const DISTRICT_NAME_ALIASES = {
  // Bifurcated districts (mapped to Census 2011 parent boundary)
  'Ranipet': 'Vellore',
  'Palghar': 'Thane',
  'Paschim Bardhaman': 'Barddhaman',

  // Renamed administrative districts
  'Bengaluru Urban': 'Bangalore',
  'Bengaluru Rural': 'Bangalore Rural',
  'Prayagraj': 'Allahabad',
  'Belagavi': 'Belgaum',
  'Mysuru': 'Mysore',
  'Tumakuru': 'Tumkur',

  // Transliteration & spelling variants
  'Ahmedabad': 'Ahmadabad',
  'Kanchipuram': 'Kancheepuram',
  'Tiruvallur': 'Thiruvallur',
  'Howrah': 'Haora',
};

// Normalized lowercase lookup table for robust case-insensitive matching
const LOWERCASE_ALIAS_MAP = Object.entries(DISTRICT_NAME_ALIASES).reduce((acc, [k, v]) => {
  acc[k.trim().toLowerCase()] = v.trim().toLowerCase();
  return acc;
}, {});

/**
 * Normalizes an API district name to match the GeoJSON DISTRICT property.
 * 
 * @param {string} apiDistrictName - Raw district name from API
 * @returns {string} Normalized district name in lowercase
 */
export function normalizeDistrictName(apiDistrictName) {
  if (!apiDistrictName) return '';
  const clean = apiDistrictName.trim().toLowerCase();
  return LOWERCASE_ALIAS_MAP[clean] || clean;
}
