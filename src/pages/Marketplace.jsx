import React, { useState, useEffect, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './Marketplace.css';

// Fix Leaflet default marker icons (they break with bundlers)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons by color
const createIcon = (color) =>
  new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

const icons = {
  company: createIcon('green'),
  default: createIcon('blue'),
  selected: createIcon('gold'),
};

// Offset overlapping markers so all are visible
function jitterCoords(companies) {
  const seen = {};
  return companies.map((c) => {
    const key = `${c.latitude.toFixed(4)},${c.longitude.toFixed(4)}`;
    if (!seen[key]) seen[key] = 0;
    const offset = seen[key] * 0.012; // ~1.3 km offset per overlap
    seen[key]++;
    if (offset === 0) return c;
    // Spread in a circle around the original point
    const angle = (seen[key] - 1) * (2.4); // golden angle in radians
    return {
      ...c,
      latitude: c.latitude + offset * Math.cos(angle),
      longitude: c.longitude + offset * Math.sin(angle),
    };
  });
}

// Haversine distance (km)
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// Component to fly map to bounds when data changes
function FitBounds({ companies }) {
  const map = useMap();
  useEffect(() => {
    if (companies.length > 0) {
      const bounds = L.latLngBounds(companies.map((c) => [c.latitude, c.longitude]));
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 7 });
    }
  }, [companies, map]);
  return null;
}

const Marketplace = () => {
  const [companies, setCompanies] = useState([]);
  const [industries, setIndustries] = useState([]);
  const [industryFilter, setIndustryFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('map'); // 'map' or 'list'
  const mapRef = useRef(null);

  // Get current user from localStorage (enriched with lat/lng from API)
  const rawUser = useMemo(() => {
    try {
      const data = localStorage.getItem('user');
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  }, []);

  const currentUser = useMemo(() => {
    if (!rawUser) return null;
    if (rawUser.latitude && rawUser.longitude) return rawUser;
    const self = companies.find((c) => c.id === rawUser.id);
    if (self) return { ...rawUser, latitude: self.latitude, longitude: self.longitude };
    return rawUser;
  }, [rawUser, companies]);

  // Fetch companies
  useEffect(() => {
    const fetchCompanies = async () => {
      setLoading(true);
      try {
        const url =
          industryFilter && industryFilter !== 'all'
            ? `/api/companies/map?industry=${encodeURIComponent(industryFilter)}`
            : '/api/companies/map';
        const res = await fetch(url);
        const data = await res.json();
        setCompanies(data.companies || []);
        if (data.industries) setIndustries(data.industries);
      } catch (err) {
        console.error('Failed to load companies:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCompanies();
  }, [industryFilter]);

  // Filter by search term
  const filteredCompanies = useMemo(() => {
    if (!searchTerm) return companies;
    const q = searchTerm.toLowerCase();
    return companies.filter(
      (c) =>
        c.company_name?.toLowerCase().includes(q) ||
        c.location?.toLowerCase().includes(q) ||
        c.industry_type?.toLowerCase().includes(q)
    );
  }, [companies, searchTerm]);

  // Jitter overlapping markers so all are visible
  const jitteredCompanies = useMemo(() => jitterCoords(filteredCompanies), [filteredCompanies]);

  // Compute distances from current user's company location
  const companiesWithDistance = useMemo(() => {
    const lat = currentUser?.latitude;
    const lng = currentUser?.longitude;
    if (!lat || !lng) return jitteredCompanies.map((c) => ({ ...c, distance: null }));
    return jitteredCompanies.map((c) => ({
      ...c,
      distance: haversine(lat, lng, c.latitude, c.longitude),
    }));
  }, [jitteredCompanies, currentUser]);

  // India center
  const center = [22.5, 78.5];

  return (
    <div className="marketplace">
      <section className="marketplace-hero">
        <div className="container">
          <h1>Industry Network Map</h1>
          <p className="subtitle">
            Explore {companies.length} companies across India. Find potential partners for waste exchange.
          </p>
        </div>
      </section>

      <section className="marketplace-content">
        <div className="container">
          {/* Toolbar */}
          <div className="map-toolbar">
            <div className="toolbar-left">
              <div className="search-bar">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  placeholder="Search companies, cities, or industries..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
              </div>
              <select
                className="industry-select"
                value={industryFilter}
                onChange={(e) => setIndustryFilter(e.target.value)}
              >
                <option value="all">All Industries ({companies.length})</option>
                {industries.map((ind) => (
                  <option key={ind} value={ind}>
                    {ind}
                  </option>
                ))}
              </select>
            </div>
            <div className="toolbar-right">
              <div className="view-toggle">
                <button
                  className={`toggle-btn ${view === 'map' ? 'active' : ''}`}
                  onClick={() => setView('map')}
                >
                  🗺️ Map
                </button>
                <button
                  className={`toggle-btn ${view === 'list' ? 'active' : ''}`}
                  onClick={() => setView('list')}
                >
                  📋 List
                </button>
              </div>
              <span className="result-count">{filteredCompanies.length} companies</span>
            </div>
          </div>

          {/* Map + sidebar layout */}
          <div className="map-layout">
            {view === 'map' && (
              <div className="map-container">
                {loading ? (
                  <div className="map-loading">Loading map data...</div>
                ) : (
                  <MapContainer
                    center={center}
                    zoom={5}
                    className="leaflet-map"
                    ref={mapRef}
                    scrollWheelZoom={true}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <FitBounds companies={filteredCompanies} />

                    {/* Your company marker (green) */}
                    {currentUser?.latitude && currentUser?.longitude && (
                      <Marker
                        position={[currentUser.latitude, currentUser.longitude]}
                        icon={icons.company}
                        zIndexOffset={1000}
                      >
                        <Popup>
                          <div className="map-popup own">
                            <strong>🏢 Your Company</strong>
                            <p>{currentUser.company_name}</p>
                            <span className="popup-badge">{currentUser.industry_type}</span>
                          </div>
                        </Popup>
                      </Marker>
                    )}

                    {/* Company markers */}
                    {companiesWithDistance.map((company) => {
                      if (company.id === currentUser?.id) return null;
                      return (
                        <Marker
                          key={company.id}
                          position={[company.latitude, company.longitude]}
                          icon={
                            selectedCompany?.id === company.id ? icons.selected : icons.default
                          }
                          eventHandlers={{
                            click: () => setSelectedCompany(company),
                          }}
                        >
                          <Popup>
                            <div className="map-popup">
                              <strong>{company.company_name}</strong>
                              <span className="popup-badge">{company.industry_type}</span>
                              <p className="popup-location">📍 {company.location}</p>
                              {company.distance != null && (
                                <p className="popup-distance">
                                  📏 {company.distance.toFixed(0)} km from you
                                </p>
                              )}
                            </div>
                          </Popup>
                        </Marker>
                      );
                    })}
                  </MapContainer>
                )}
              </div>
            )}

            {/* Company list / sidebar */}
            <div className={`company-list ${view === 'list' ? 'full-width' : ''}`}>
              <h3 className="list-title">
                {view === 'list' ? 'All Companies' : 'Companies'}
                <span className="list-count">{filteredCompanies.length}</span>
              </h3>
              <div className="company-cards">
                {companiesWithDistance
                  .filter((c) => c.id !== currentUser?.id)
                  .sort((a, b) => (a.distance ?? 9999) - (b.distance ?? 9999))
                  .map((company) => (
                    <div
                      key={company.id}
                      className={`company-card-item ${
                        selectedCompany?.id === company.id ? 'selected' : ''
                      }`}
                      onClick={() => setSelectedCompany(company)}
                    >
                      <div className="card-top-row">
                        <div className="card-avatar">
                          {company.company_name?.[0]?.toUpperCase() || '?'}
                        </div>
                        <div className="card-info">
                          <h4>{company.company_name}</h4>
                          <span className="card-industry">{company.industry_type}</span>
                        </div>
                        {company.distance != null && (
                          <span className="card-distance">
                            {company.distance < 1
                              ? '< 1 km'
                              : `${company.distance.toFixed(0)} km`}
                          </span>
                        )}
                      </div>
                      <div className="card-bottom-row">
                        <span className="card-location">📍 {company.location}</span>
                        <div className="card-stats-mini">
                          <span title="Classifications">📸 {company.classifications_count || 0}</span>
                          <span title="Listings">🏷️ {company.listings_count || 0}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                {filteredCompanies.length === 0 && !loading && (
                  <div className="no-results-compact">
                    <p>No companies found matching your filters.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Marketplace;