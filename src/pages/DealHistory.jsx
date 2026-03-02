import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './DealHistory.css';

const DealHistory = () => {
  const navigate = useNavigate();
  const [user] = useState(() => {
    try {
      const d = localStorage.getItem('user');
      return d ? JSON.parse(d) : null;
    } catch { return null; }
  });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');         // all | active | completed | cancelled
  const [wasteFilter, setWasteFilter] = useState('all');
  const [renderTime] = useState(() => Date.now());

  useEffect(() => {
    if (!user) { navigate('/login'); return; }
  }, [user, navigate]);

  useEffect(() => {
    if (!user?.id) return;
    fetch(`/api/deals/analytics/${user.id}`)
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [user?.id]);

  /* ── Filtered deals ── */
  const filteredDeals = useMemo(() => {
    if (!data?.deals) return [];
    return data.deals.filter(d => {
      if (filter !== 'all' && d.status !== filter) return false;
      if (wasteFilter !== 'all' && d.waste_type !== wasteFilter) return false;
      return true;
    });
  }, [data, filter, wasteFilter]);

  /* ── Unique waste types for filter ── */
  const wasteTypes = useMemo(() => {
    if (!data?.deals) return [];
    return [...new Set(data.deals.map(d => d.waste_type))].sort();
  }, [data]);

  /* ── Chart bar helpers ── */
  const maxBarValue = useMemo(() => {
    if (!data?.by_waste_type?.length) return 1;
    return Math.max(...data.by_waste_type.map(w => w.count), 1);
  }, [data]);

  const maxMonthValue = useMemo(() => {
    if (!data?.by_month?.length) return 1;
    return Math.max(...data.by_month.map(m => m.total), 1);
  }, [data]);

  /* ── Helpers ── */
  const statusEmoji = (s) => s === 'active' ? '🟢' : s === 'completed' ? '✅' : '❌';
  const statusLabel = (s) => s === 'active' ? 'Active' : s === 'completed' ? 'Completed' : 'Cancelled';

  const formatDate = (iso) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const formatCurrency = (v) => `₹${Number(v || 0).toLocaleString('en-IN')}`;

  const getPartnerName = (deal) => {
    if (!user) return '';
    return deal.proposer_id === user.id ? deal.responder_name : deal.proposer_name;
  };

  const getDirection = (deal) => {
    if (!user) return '';
    if (deal.proposer_id === user.id) return deal.direction === 'sell' ? 'Selling' : 'Buying';
    return deal.direction === 'sell' ? 'Buying' : 'Selling';
  };

  const timeAgo = (iso) => {
    if (!iso) return '';
    const diff = (renderTime - new Date(iso).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  };

  const activityIcon = (type) => {
    switch (type) {
      case 'deal_proposed':  return '📝';
      case 'deal_completed': return '✅';
      case 'deal_accepted':  return '🤝';
      case 'deal_cancelled': return '❌';
      default:               return '📌';
    }
  };

  const activityLabel = (type) => {
    switch (type) {
      case 'deal_proposed':  return 'Deal Proposed';
      case 'deal_completed': return 'Deal Completed';
      case 'deal_accepted':  return 'Deal Accepted';
      case 'deal_cancelled': return 'Deal Cancelled';
      default:               return type;
    }
  };

  const dbInfo = [
    { key: 'postgresql', label: 'PostgreSQL', icon: '🐘', color: '#336791' },
    { key: 'neo4j',      label: 'Neo4j',      icon: '🔗', color: '#018bff' },
    { key: 'cassandra',  label: 'Cassandra',  icon: '⏱️', color: '#1287b1' },
    { key: 'mongodb',    label: 'MongoDB',    icon: '🍃', color: '#47a248' },
    { key: 'redis',      label: 'Redis',      icon: '⚡', color: '#dc382d' },
  ];

  if (loading) return <div className="loading">Loading…</div>;
  if (!user) return null;

  const s = data?.stats || {};

  return (
    <div className="deal-history">
      {/* ── Hero ── */}
      <section className="dh-hero">
        <div className="container">
          <div className="dh-hero-content">
            <div>
              <p className="dh-hero-sub">Deal Analytics</p>
              <h1>Your Deal History</h1>
              <p className="dh-hero-desc">Track every deal, monitor trends, and see your impact over time.</p>
            </div>
            <div className="dh-hero-quick">
              <div className="dh-quick-stat">
                <span className="dh-quick-val">{s.total || 0}</span>
                <span className="dh-quick-lbl">Total Deals</span>
              </div>
              <div className="dh-quick-stat">
                <span className="dh-quick-val">{s.completed || 0}</span>
                <span className="dh-quick-lbl">Completed</span>
              </div>
              <div className="dh-quick-stat">
                <span className="dh-quick-val">{formatCurrency(s.total_value)}</span>
                <span className="dh-quick-lbl">Total Value</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── DB Badges Ribbon ── */}
      {data?.db_sources && (
        <section className="dh-db-ribbon">
          <div className="container">
            <div className="dh-db-strip">
              <span className="dh-db-label">Powered by 5 Databases</span>
              <div className="dh-db-badges">
                {dbInfo.map(db => (
                  <span
                    key={db.key}
                    className={`dh-db-badge ${data.db_sources[db.key] ? 'dh-db-active' : 'dh-db-inactive'}`}
                    style={data.db_sources[db.key] ? { '--db-color': db.color } : {}}
                  >
                    <span className="dh-db-dot"></span>
                    {db.icon} {db.label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="dh-body">
        <div className="container">

          {/* ── Stat Cards ── */}
          <div className="dh-stats-grid">
            <div className="dh-stat-card dh-stat-green">
              <div className="dh-stat-icon">🟢</div>
              <div className="dh-stat-info">
                <span className="dh-stat-val">{s.active || 0}</span>
                <span className="dh-stat-lbl">Active Deals</span>
              </div>
            </div>
            <div className="dh-stat-card dh-stat-blue">
              <div className="dh-stat-icon">✅</div>
              <div className="dh-stat-info">
                <span className="dh-stat-val">{s.completed || 0}</span>
                <span className="dh-stat-lbl">Completed</span>
              </div>
            </div>
            <div className="dh-stat-card dh-stat-red">
              <div className="dh-stat-icon">❌</div>
              <div className="dh-stat-info">
                <span className="dh-stat-val">{s.cancelled || 0}</span>
                <span className="dh-stat-lbl">Cancelled</span>
              </div>
            </div>
            <div className="dh-stat-card dh-stat-purple">
              <div className="dh-stat-icon">⚖️</div>
              <div className="dh-stat-info">
                <span className="dh-stat-val">{Number(s.waste_traded || 0).toFixed(1)}t</span>
                <span className="dh-stat-lbl">Waste Traded</span>
              </div>
            </div>
            <div className="dh-stat-card dh-stat-gold">
              <div className="dh-stat-icon">💰</div>
              <div className="dh-stat-info">
                <span className="dh-stat-val">{formatCurrency(s.total_value)}</span>
                <span className="dh-stat-lbl">Total Value</span>
              </div>
            </div>
            <div className="dh-stat-card dh-stat-teal">
              <div className="dh-stat-icon">🌍</div>
              <div className="dh-stat-info">
                <span className="dh-stat-val">{Number(s.co2_saved || 0).toFixed(1)}t</span>
                <span className="dh-stat-lbl">CO₂ Saved</span>
              </div>
            </div>
          </div>

          {/* ── Redis: Live Platform Stats ── */}
          {data?.redis_live && Object.keys(data.redis_live).length > 0 && (
            <div className="dh-card dh-redis-card">
              <h3><span className="dh-db-source-tag" style={{ background: '#dc382d' }}>⚡ Redis</span> Live Platform Stats</h3>
              <p className="dh-redis-subtitle">Real-time counters across all users on the platform</p>
              <div className="dh-redis-grid">
                <div className="dh-redis-item">
                  <span className="dh-redis-val">{data.redis_live.total_proposed || 0}</span>
                  <span className="dh-redis-lbl">📝 Deals Proposed</span>
                </div>
                <div className="dh-redis-item">
                  <span className="dh-redis-val">{data.redis_live.total_completed || 0}</span>
                  <span className="dh-redis-lbl">✅ Deals Completed</span>
                </div>
                <div className="dh-redis-item">
                  <span className="dh-redis-val">{Number(data.redis_live.total_quantity || 0).toFixed(1)}t</span>
                  <span className="dh-redis-lbl">⚖️ Waste Traded</span>
                </div>
                <div className="dh-redis-item">
                  <span className="dh-redis-val">{formatCurrency(data.redis_live.total_value)}</span>
                  <span className="dh-redis-lbl">💰 Total Value</span>
                </div>
              </div>
            </div>
          )}

          {/* ── Charts Row ── */}
          <div className="dh-charts-row">
            {/* Waste-type breakdown */}
            <div className="dh-card">
              <h3>📦 By Waste Type</h3>
              {data?.by_waste_type?.length > 0 ? (
                <div className="dh-bar-chart">
                  {data.by_waste_type.map(w => (
                    <div key={w.waste_type} className="dh-bar-row">
                      <span className="dh-bar-label">{w.waste_type}</span>
                      <div className="dh-bar-track">
                        <div className="dh-bar-fill" style={{ width: `${(w.count / maxBarValue) * 100}%` }}>
                          <span className="dh-bar-val">{w.count}</span>
                        </div>
                      </div>
                      <span className="dh-bar-extra">{formatCurrency(w.value)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="dh-empty-text">No deals yet</p>
              )}
            </div>

            {/* Monthly trend */}
            <div className="dh-card">
              <h3>📈 Monthly Trend</h3>
              {data?.by_month?.length > 0 ? (
                <div className="dh-month-chart">
                  {data.by_month.map(m => (
                    <div key={m.month} className="dh-month-col">
                      <div className="dh-month-bar-wrap">
                        <div
                          className="dh-month-bar"
                          style={{ height: `${(m.total / maxMonthValue) * 100}%` }}
                          title={`${m.total} deals (${m.completed} completed)`}
                        >
                          {m.completed > 0 && (
                            <div
                              className="dh-month-bar-completed"
                              style={{ height: `${(m.completed / m.total) * 100}%` }}
                            />
                          )}
                        </div>
                      </div>
                      <span className="dh-month-label">{m.month.slice(5)}</span>
                      <span className="dh-month-count">{m.total}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="dh-empty-text">No monthly data yet</p>
              )}
              {data?.by_month?.length > 0 && (
                <div className="dh-month-legend">
                  <span className="dh-legend-item"><span className="dh-legend-box dh-legend-total"></span>Total</span>
                  <span className="dh-legend-item"><span className="dh-legend-box dh-legend-completed"></span>Completed</span>
                </div>
              )}
            </div>
          </div>

          {/* ── Top Partners ── */}
          {data?.partners?.length > 0 && (
            <div className="dh-card">
              <h3>🤝 Top Deal Partners</h3>
              <div className="dh-partners-grid">
                {data.partners.map(p => (
                  <div key={p.id} className="dh-partner-card">
                    <div className="dh-partner-avatar">
                      {(p.name || '?')[0].toUpperCase()}
                    </div>
                    <div className="dh-partner-info">
                      <span className="dh-partner-name">{p.name}</span>
                      <span className="dh-partner-meta">{p.industry} • {p.location || 'India'}</span>
                    </div>
                    <div className="dh-partner-stats">
                      <span className="dh-partner-count">{p.deal_count} deals</span>
                      <span className="dh-partner-value">{formatCurrency(p.total_value)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Cassandra + MongoDB Row ── */}
          <div className="dh-charts-row">
            {/* ── Cassandra: Deal Event Timeline ── */}
            <div className="dh-card dh-cass-card">
              <h3><span className="dh-db-source-tag" style={{ background: '#1287b1' }}>⏱️ Cassandra</span> Deal Event Timeline</h3>
              {data?.cassandra_timeline?.length > 0 ? (
                <div className="dh-timeline">
                  {data.cassandra_timeline.map((ev, i) => (
                    <div key={i} className={`dh-tl-item dh-tl-${ev.type === 'deal_completed' ? 'completed' : 'proposed'}`}>
                      <div className="dh-tl-dot"></div>
                      <div className="dh-tl-content">
                        <span className="dh-tl-type">
                          {ev.type === 'deal_completed' ? '✅ Completed' : '📝 Proposed'}
                        </span>
                        <span className="dh-tl-meta">
                          {ev.waste_type} • {Number(ev.quantity || 0).toFixed(1)}t
                        </span>
                        <span className="dh-tl-time">{timeAgo(ev.timestamp)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="dh-empty-text">No time-series events recorded yet. Complete deals to see the timeline!</p>
              )}
            </div>

            {/* ── MongoDB: Activity Feed ── */}
            <div className="dh-card dh-mongo-card">
              <h3><span className="dh-db-source-tag" style={{ background: '#47a248' }}>🍃 MongoDB</span> Activity Feed</h3>
              {data?.mongo_activity?.length > 0 ? (
                <div className="dh-activity-feed">
                  {data.mongo_activity.map((a, i) => (
                    <div key={i} className="dh-feed-item">
                      <span className="dh-feed-icon">{activityIcon(a.type)}</span>
                      <div className="dh-feed-body">
                        <span className="dh-feed-title">{activityLabel(a.type)}</span>
                        <span className="dh-feed-detail">
                          {a.waste_type && `${a.waste_type}`}
                          {a.quantity ? ` • ${Number(a.quantity).toFixed(1)}t` : ''}
                          {a.total_price ? ` • ${formatCurrency(a.total_price)}` : ''}
                          {a.co2_saved ? ` • 🌍 ${Number(a.co2_saved).toFixed(1)}t CO₂` : ''}
                        </span>
                      </div>
                      <span className="dh-feed-time">{timeAgo(a.created_at)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="dh-empty-text">No activity recorded yet. Start making deals!</p>
              )}
            </div>
          </div>

          {/* ── Deal Table ── */}
          <div className="dh-card dh-table-card">
            <div className="dh-table-header">
              <h3>📋 All Deals</h3>
              <div className="dh-filters">
                <select value={filter} onChange={e => setFilter(e.target.value)} className="dh-filter-select">
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
                <select value={wasteFilter} onChange={e => setWasteFilter(e.target.value)} className="dh-filter-select">
                  <option value="all">All Types</option>
                  {wasteTypes.map(wt => <option key={wt} value={wt}>{wt}</option>)}
                </select>
              </div>
            </div>

            {filteredDeals.length === 0 ? (
              <div className="dh-empty">
                <span className="dh-empty-icon">📭</span>
                <p>No deals match the current filters</p>
                {filter !== 'all' || wasteFilter !== 'all' ? (
                  <button className="dh-reset-btn" onClick={() => { setFilter('all'); setWasteFilter('all'); }}>Reset Filters</button>
                ) : (
                  <Link to="/chat" className="dh-reset-btn">Start a conversation to create deals</Link>
                )}
              </div>
            ) : (
              <div className="dh-table-wrap">
                <table className="dh-table">
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Partner</th>
                      <th>Type</th>
                      <th>Direction</th>
                      <th>Quantity</th>
                      <th>Total Value</th>
                      <th>Created</th>
                      <th>Resolved</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDeals.map(deal => (
                      <tr key={deal.id} className={`dh-row dh-row-${deal.status}`}>
                        <td>
                          <span className={`dh-status-pill dh-pill-${deal.status}`}>
                            {statusEmoji(deal.status)} {statusLabel(deal.status)}
                          </span>
                        </td>
                        <td className="dh-cell-partner">
                          <span className="dh-partner-mini-avatar">
                            {(getPartnerName(deal) || '?')[0].toUpperCase()}
                          </span>
                          {getPartnerName(deal)}
                        </td>
                        <td>{deal.waste_type}</td>
                        <td>
                          <span className={`dh-dir-tag ${getDirection(deal) === 'Selling' ? 'dh-dir-sell' : 'dh-dir-buy'}`}>
                            {getDirection(deal) === 'Selling' ? '📤' : '📥'} {getDirection(deal)}
                          </span>
                        </td>
                        <td>{Number(deal.quantity).toFixed(1)} {deal.unit}</td>
                        <td className="dh-cell-value">{formatCurrency(deal.total_price)}</td>
                        <td>{formatDate(deal.created_at)}</td>
                        <td>{formatDate(deal.completed_at || deal.cancelled_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {filteredDeals.length > 0 && (
              <div className="dh-table-footer">
                Showing {filteredDeals.length} of {data?.deals?.length || 0} deals
              </div>
            )}
          </div>

        </div>
      </section>
    </div>
  );
};

export default DealHistory;
