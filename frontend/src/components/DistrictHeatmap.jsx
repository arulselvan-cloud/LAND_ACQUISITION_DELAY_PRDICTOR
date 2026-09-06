import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { DISTRICT_NAME_ALIASES, normalizeDistrictName } from '../constants/districtAliases';
import { MapPin, Info, Layers } from 'lucide-react';

// Color scale mapping average delay probability to choropleth tones
function getRiskColor(delayProb) {
  if (delayProb === undefined || delayProb === null) return '#CBD5E1'; // Unmonitored slate
  if (delayProb >= 0.65) return '#DC2626'; // Deep Crimson (Critical delay cluster)
  if (delayProb >= 0.50) return '#EA580C'; // Bright Orange (High delay risk)
  if (delayProb >= 0.35) return '#F59E0B'; // Amber (Medium delay risk)
  return '#10B981'; // Emerald (Low risk / On schedule)
}

export default function DistrictHeatmap({
  districtsSummary = [],
  geoJsonData = null,
  onSelectDistrict = () => {},
  selectedDistrict = null,
}) {
  const [geoData, setGeoData] = useState(geoJsonData);
  const [loadingGeo, setLoadingGeo] = useState(!geoJsonData);
  const [unmatchedDistricts, setUnmatchedDistricts] = useState([]);

  // Load dists11.geojson from public folder if not passed via props
  useEffect(() => {
    if (geoJsonData) {
      setGeoData(geoJsonData);
      setLoadingGeo(false);
      return;
    }

    setLoadingGeo(true);
    fetch('/dists11.geojson')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setGeoData(data);
        setLoadingGeo(false);
      })
      .catch((err) => {
        console.warn('Could not load /dists11.geojson:', err);
        setLoadingGeo(false);
      });
  }, [geoJsonData]);

  // Build fast normalized lookup dictionary from API district summary
  const summaryByDistrictName = useMemo(() => {
    const map = new Map();
    districtsSummary.forEach((item) => {
      const norm = normalizeDistrictName(item.district);
      map.set(norm, item);
    });
    return map;
  }, [districtsSummary]);

  // Check and log any district from API that fails to match a polygon
  useEffect(() => {
    if (!geoData || !districtsSummary.length) return;

    const geoDistrictNames = new Set(
      geoData.features.map((f) => (f.properties?.DISTRICT || '').trim().toLowerCase())
    );

    const missing = [];
    districtsSummary.forEach((item) => {
      const norm = normalizeDistrictName(item.district);
      if (!geoDistrictNames.has(norm)) {
        missing.push(item.district);
      }
    });

    setUnmatchedDistricts(missing);

    if (missing.length > 0) {
      console.warn(
        `[DistrictHeatmap] Unmatched Districts from API (${missing.length}/${districtsSummary.length}):`,
        missing
      );
    } else {
      console.log(
        `[DistrictHeatmap] 100% Match: All ${districtsSummary.length}/${districtsSummary.length} API districts matched GeoJSON polygons.`
      );
    }
  }, [geoData, districtsSummary]);

  // Styling function for each district polygon feature
  const styleFeature = (feature) => {
    const geoName = (feature.properties?.DISTRICT || '').trim().toLowerCase();
    const data = summaryByDistrictName.get(geoName);

    const hasData = !!data;
    const isSelected = selectedDistrict && normalizeDistrictName(selectedDistrict) === geoName;

    return {
      fillColor: getRiskColor(data?.avg_delay_probability),
      weight: isSelected ? 3 : hasData ? 1.5 : 0.4,
      opacity: 1,
      color: isSelected ? '#0F2537' : hasData ? '#475569' : '#CBD5E1',
      fillOpacity: hasData ? (isSelected ? 0.9 : 0.75) : 0.15,
      dashArray: isSelected ? '3' : '',
    };
  };

  // Attach tooltips and click events to each polygon
  const onEachFeature = (feature, layer) => {
    const geoName = (feature.properties?.DISTRICT || '').trim().toLowerCase();
    const displayName = feature.properties?.DISTRICT || 'Unknown District';
    const stateName = feature.properties?.ST_NM || '';
    const data = summaryByDistrictName.get(geoName);

    if (data) {
      const tooltipContent = `
        <div style="font-family: inherit; font-size: 0.76rem; line-height: 1.35; padding: 2px;">
          <div style="font-weight: 800; color: #0F172A; font-size: 0.85rem;">${data.district}</div>
          <div style="color: #64748B; font-size: 0.72rem; margin-bottom: 4px;">${data.state || stateName}</div>
          <div style="display: flex; justify-content: space-between; gap: 12px; margin-top: 4px;">
            <span style="color: #475569;">Avg Delay Risk:</span>
            <strong style="color: ${getRiskColor(data.avg_delay_probability)};">${(data.avg_delay_probability * 100).toFixed(1)}%</strong>
          </div>
          <div style="display: flex; justify-content: space-between; gap: 12px;">
            <span style="color: #475569;">Active Projects:</span>
            <strong>${data.project_count}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; gap: 12px;">
            <span style="color: #475569;">Critical Bottlenecks:</span>
            <strong style="color: #DC2626;">${data.critical_risk_count}</strong>
          </div>
          <div style="margin-top: 6px; font-size: 0.68rem; color: #1E56A0; font-weight: 600;">
            Click to filter projects
          </div>
        </div>
      `;
      layer.bindTooltip(tooltipContent, {
        sticky: true,
        className: 'gov-map-tooltip',
      });

      layer.on({
        click: () => {
          onSelectDistrict(data.district);
        },
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({ weight: 3, color: '#1E56A0', fillOpacity: 0.9 });
          l.bringToFront();
        },
        mouseout: (e) => {
          const l = e.target;
          l.setStyle(styleFeature(feature));
        },
      });
    }
  };

  return (
    <div className="card heatmap-card">
      <div className="card-header">
        <div>
          <h2 className="card-title">
            <MapPin size={18} className="text-gov-blue" />
            Geospatial Delay Risk Heatmap
          </h2>
          <p className="card-subtitle">
            District-level delay exposure choropleth across statutory RFCTLARR acquisition zones
          </p>
        </div>

        {selectedDistrict && (
          <button
            onClick={() => onSelectDistrict(null)}
            className="chip-btn active"
            style={{ fontSize: '0.74rem', background: '#0F2537' }}
          >
            Filtered: {selectedDistrict} (Clear)
          </button>
        )}
      </div>

      <div className="map-container">
        {loadingGeo ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
            Loading India 641 District Boundaries...
          </div>
        ) : (
          <MapContainer
            center={[22.5, 78.9]}
            zoom={4.5}
            minZoom={3}
            scrollWheelZoom={false}
            style={{ height: '100%', width: '100%', background: '#E2E8F0' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {geoData && (
              <GeoJSON
                data={geoData}
                style={styleFeature}
                onEachFeature={onEachFeature}
              />
            )}
          </MapContainer>
        )}

        {/* Choropleth Legend */}
        <div className="map-legend">
          <div className="map-legend-title">Delay Probability Scale</div>
          <div className="legend-scale">
            <div className="legend-bar" style={{ background: '#10B981' }} title="< 35% Low Risk" />
            <span style={{ marginRight: '6px' }}>&lt;35%</span>
            <div className="legend-bar" style={{ background: '#F59E0B' }} title="35-50% Medium Risk" />
            <span style={{ marginRight: '6px' }}>50%</span>
            <div className="legend-bar" style={{ background: '#EA580C' }} title="50-65% High Risk" />
            <span style={{ marginRight: '6px' }}>65%</span>
            <div className="legend-bar" style={{ background: '#DC2626' }} title="> 65% Critical Delay" />
            <span>&gt;65%</span>
          </div>
          <div style={{ marginTop: '4px', fontSize: '0.68rem', color: '#64748B' }}>
            52 Monitored Districts Highlighted
          </div>
        </div>
      </div>
    </div>
  );
}
export { DISTRICT_NAME_ALIASES };
