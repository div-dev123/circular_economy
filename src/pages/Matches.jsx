import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import './Matches.css';

const WASTE_LABELS = {
  metal: '🔩 Metal',
  plastic: '♳ Plastic',
  'paper/cardboard': '📦 Paper / Cardboard',
  glass: '🫙 Glass',
  organic: '🌿 Organic',
  textile: '🧵 Textile',
  construction: '🧱 Construction',
  hazardous: '☣️ Hazardous',
  'industrial ash': 'ite Industrial Ash',
  electronic: '💻 Electronic',
  mixed: '🔀 Mixed',
};

const scoreColor = (v) => {
  if (v >= 75) return 'score-excellent';
  if (v >= 55) return 'score-good';
  if (v >= 35) return 'score-moderate';
  return 'score-low';
};

const Matches = () => {
  const [wasteType, setWasteType] = useState('metal');
  const [wasteTypes, setWasteTypes] = useState([]);
  const [matches, setMatches] = useState([]);
  const [weights, setWeights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [quantity, setQuantity] = useState(1);

  const currentUser = useMemo(() => {
    try {
      const d = localStorage.getItem('user');
      return d ? JSON.parse(d) : null;
    } catch {
      return null;
    }
  }, []);

  // Fetch matches whenever waste type or quantity changes
  useEffect(() => {
    const fetchMatches = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ waste_type: wasteType, quantity: String(quantity), top_k: '15' });
        if (currentUser?.id) params.append('user_id', String(currentUser.id));
        const res = await fetch(`/api/smart-match?${params}`);
        const data = await res.json();
        setMatches(data.matches || []);
        if (data.waste_types) setWasteTypes(data.waste_types);
        if (data.weights) setWeights(data.weights);
      } catch (err) {
        console.error('Failed to load matches:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMatches();
  }, [wasteType, quantity, currentUser]);

  return (
    <div className="matches-page">
      {/* Hero */}
      <section className="matches-hero">
        <div className="container">
          <h1>AI Material Matching</h1>
          <p className="subtitle">
            Our hybrid ML + rule-based engine finds the best companies to process your waste — scored by
            compatibility, proximity, and demand.
          </p>
        </div>
      </section>

      <section className="matches-content">
        <div className="container">
          {/* Algorithm explainer */}
          {weights && (
            <div className="algo-bar">
              <span className="algo-tag">🧠 Hybrid Algorithm</span>
              <div className="algo-weights">
                <span className="weight-pill rule">Rule-Based {weights.rule_based}%</span>
                <span className="weight-pill ml">ML Similarity {weights.ml_similarity}%</span>
                <span className="weight-pill knn">KNN Clustering {weights.knn_clustering}%</span>
                <span className="weight-pill dist">Distance {weights.distance}%</span>
              </div>
            </div>
          )}

          {/* Controls */}
          <div className="match-controls">
            <div className="control-group">
              <label htmlFor="waste-select">Waste Type</label>
              <select
                id="waste-select"
                value={wasteType}
                onChange={(e) => setWasteType(e.target.value)}
                className="match-select"
              >
                {(wasteTypes.length ? wasteTypes : Object.keys(WASTE_LABELS)).map((wt) => (
                  <option key={wt} value={wt}>
                    {WASTE_LABELS[wt] || wt}
                  </option>
                ))}
              </select>
            </div>

            <div className="control-group">
              <label htmlFor="qty-input">Quantity (tons)</label>
              <input
                id="qty-input"
                type="number"
                min="0.1"
                step="0.5"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(0.1, Number(e.target.value)))}
                className="match-input"
              />
            </div>

            <div className="control-summary">
              <span className="result-badge">
                {loading ? '…' : `${matches.length} matches`}
              </span>
            </div>
          </div>

          {/* Results */}
          {loading ? (
            <div className="match-loading">
              <div className="spinner" />
              <p>Running matching algorithm…</p>
            </div>
          ) : matches.length === 0 ? (
            <div className="match-empty">
              <span className="empty-icon">🔍</span>
              <h3>No matches found</h3>
              <p>Try selecting a different waste type or adjusting the quantity.</p>
            </div>
          ) : (
            <div className="match-results">
              {matches.map((m, idx) => (
                <div
                  key={m.id}
                  className={`match-card ${expandedId === m.id ? 'expanded' : ''}`}
                  onClick={() => setExpandedId(expandedId === m.id ? null : m.id)}
                >
                  {/* Rank badge */}
                  <div className={`rank-badge ${idx < 3 ? 'top' : ''}`}>
                    {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `#${idx + 1}`}
                  </div>

                  {/* Card header */}
                  <div className="match-card-header">
                    <div className="mc-avatar">{m.company_name?.[0]?.toUpperCase() || '?'}</div>
                    <div className="mc-info">
                      <h3>{m.company_name}</h3>
                      <span className="mc-industry">{m.industry_type}</span>
                      <span className="mc-location">📍 {m.location}</span>
                    </div>
                    <div className={`mc-score ${scoreColor(m.match_score)}`}>
                      <span className="score-value">{m.match_score}</span>
                      <span className="score-label">Match</span>
                    </div>
                  </div>

                  {/* Reason */}
                  <p className="match-reason">{m.match_reason}</p>

                  {/* Score breakdown (visible when expanded) */}
                  {expandedId === m.id && (
                    <div className="score-breakdown">
                      <h4>Score Breakdown</h4>
                      <div className="breakdown-bars">
                        <ScoreBar label="Rule-Based" value={m.rule_score} icon="📏" />
                        <ScoreBar label="ML Similarity" value={m.similarity_score} icon="🧠" />
                        <ScoreBar label="KNN Cluster" value={m.knn_score} icon="🎯" />
                        <ScoreBar label="Proximity" value={m.distance_score} icon="📍" />
                      </div>
                      <div className="breakdown-meta">
                        <span>🛣️ {m.distance_km} km away</span>
                        <span>📸 {m.classifications_count || 0} classifications</span>
                        <span>🏷️ {m.listings_count || 0} listings</span>
                      </div>
                    </div>
                  )}

                  <span className="expand-hint">
                    {expandedId === m.id ? '▲ Less' : '▼ Details'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

/* ───── tiny sub-component ───── */
const ScoreBar = ({ label, value, icon }) => (
  <div className="bar-row">
    <span className="bar-label">
      {icon} {label}
    </span>
    <div className="bar-track">
      <div
        className={`bar-fill ${scoreColor(value)}`}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
    <span className="bar-value">{value}%</span>
  </div>
);

export default Matches;
