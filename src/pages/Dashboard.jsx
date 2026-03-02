import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const userData = localStorage.getItem('user');
        if (userData) {
          setUser(JSON.parse(userData));
        } else {
          navigate('/login');
        }
      }
    } catch {
      navigate('/login');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // Fetch analytics from the multi-database endpoint
  useEffect(() => {
    if (!user?.id) return;
    setAnalyticsLoading(true);
    fetch(`/api/analytics/dashboard?user_id=${user.id}`)
      .then(r => r.json())
      .then(data => {
        setAnalytics(data);
        // Refresh top stat cards with live DB values
        if (data?.user) {
          const fresh = {
            ...user,
            classifications_count: data.user.classifications ?? user.classifications_count,
            deals_completed: data.user.deals_completed ?? user.deals_completed ?? 0,
            waste_processed_tons: data.user.waste_processed ?? user.waste_processed_tons,
            co2_saved_tons: data.user.co2_saved ?? user.co2_saved_tons,
            cost_savings: data.user.cost_savings ?? user.cost_savings,
          };
          setUser(fresh);
          localStorage.setItem('user', JSON.stringify(fresh));
        }
      })
      .catch(() => setAnalytics(null))
      .finally(() => setAnalyticsLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  const joinDate = useMemo(() => {
    if (user?.created_at) {
      return new Date(user.created_at).toLocaleDateString('en-IN', {
        year: 'numeric', month: 'long', day: 'numeric',
      });
    }
    return 'Recently';
  }, [user]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  const hasActivity = user && (
    (user.classifications_count || 0) > 0 ||
    (user.deals_completed || 0) > 0 ||
    Number(user.waste_processed_tons || 0) > 0
  );

  if (loading) return <div className="loading">Loading...</div>;
  if (!user) return null;

  return (
    <div className="dashboard">
      {/* Hero */}
      <section className="dash-hero">
        <div className="container">
          <div className="dash-hero-content">
            <div className="dash-hero-text">
              <p className="dash-greeting">{getGreeting()},</p>
              <h1>{user.company_name || user.email}</h1>
              <p className="dash-subtitle">
                Your Industrial Symbiosis hub — manage waste, find partners, and track your environmental impact.
              </p>
            </div>
            <div className="dash-hero-meta">
              <span className="dash-badge">{user.industry_type || 'N/A'}</span>
              {user.location && <span className="dash-location">📍 {user.location}</span>}
            </div>
          </div>
        </div>
      </section>

      <section className="dash-body">
        <div className="container">
          {/* Stats row */}
          <div className="dash-stats">
            <div className="dash-stat-card">
              <div className="dash-stat-icon">📸</div>
              <div className="dash-stat-info">
                <span className="dash-stat-value">{user.classifications_count || 0}</span>
                <span className="dash-stat-label">Classifications</span>
              </div>
            </div>
            <div className="dash-stat-card">
              <div className="dash-stat-icon">🤝</div>
              <div className="dash-stat-info">
                <span className="dash-stat-value">{user.deals_completed || 0}</span>
                <span className="dash-stat-label">Deals Done</span>
              </div>
            </div>
            <div className="dash-stat-card">
              <div className="dash-stat-icon">⚖️</div>
              <div className="dash-stat-info">
                <span className="dash-stat-value">{Number(user.waste_processed_tons || 0).toFixed(1)}t</span>
                <span className="dash-stat-label">Waste Processed</span>
              </div>
            </div>
            <div className="dash-stat-card">
              <div className="dash-stat-icon">🌍</div>
              <div className="dash-stat-info">
                <span className="dash-stat-value">{Number(user.co2_saved_tons || 0).toFixed(1)}t</span>
                <span className="dash-stat-label">CO₂ Saved</span>
              </div>
            </div>
            <div className="dash-stat-card accent">
              <div className="dash-stat-icon">💰</div>
              <div className="dash-stat-info">
                <span className="dash-stat-value">₹{Number(user.cost_savings || 0).toFixed(0)}</span>
                <span className="dash-stat-label">Cost Savings</span>
              </div>
            </div>
          </div>

          {/* Impact prompt when no activity */}
          {!hasActivity && (
            <div className="dash-card dash-impact-empty">
              <div className="impact-empty-icon">🌱</div>
              <h3>Start Making an Impact</h3>
              <p>Classify waste or create marketplace listings to begin tracking your environmental contributions.</p>
              <div className="impact-empty-actions">
                <Link to="/classify" className="btn btn-primary">Classify Waste</Link>
                <Link to="/marketplace" className="btn btn-outline">Browse Marketplace</Link>
              </div>
            </div>
          )}

          {/* ── Live Platform Analytics (full-width, from all 5 databases) ── */}
          {analytics && (
            <div className="dash-card dash-analytics-card dash-analytics-full">
              <div className="dash-analytics-header">
                <h3>📊 Live Platform Analytics</h3>
                <div className="dash-db-badges">
                  {(analytics.nosql_sources || []).map(db => (
                    <span key={db} className={`dash-db-badge db-${db}`}>{db}</span>
                  ))}
                </div>
              </div>
              <div className="dash-analytics-grid">
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.total_users || 0}</span>
                  <span className="dash-analytics-lbl">Companies</span>
                  <span className="dash-analytics-db">PostgreSQL</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.classifications_total || 0}</span>
                  <span className="dash-analytics-lbl">Classifications</span>
                  <span className="dash-analytics-db">Redis</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.classification_docs || 0}</span>
                  <span className="dash-analytics-lbl">Stored Reports</span>
                  <span className="dash-analytics-db">MongoDB</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.matches_total || 0}</span>
                  <span className="dash-analytics-lbl">Matches Run</span>
                  <span className="dash-analytics-db">Redis</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.total_conversations || 0}</span>
                  <span className="dash-analytics-lbl">Conversations</span>
                  <span className="dash-analytics-db">PostgreSQL</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.total_messages || 0}</span>
                  <span className="dash-analytics-lbl">Messages</span>
                  <span className="dash-analytics-db">PostgreSQL</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.graph_nodes || 0}</span>
                  <span className="dash-analytics-lbl">Graph Nodes</span>
                  <span className="dash-analytics-db">Neo4j</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.graph_relationships || 0}</span>
                  <span className="dash-analytics-lbl">Relationships</span>
                  <span className="dash-analytics-db">Neo4j</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.online_users || 0}</span>
                  <span className="dash-analytics-lbl">Online Now</span>
                  <span className="dash-analytics-db">Redis</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.cache_hits || 0}</span>
                  <span className="dash-analytics-lbl">Cache Hits</span>
                  <span className="dash-analytics-db">Redis</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.classification_trend || 0}</span>
                  <span className="dash-analytics-lbl">30d Events</span>
                  <span className="dash-analytics-db">Cassandra</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.total_industries || 0}</span>
                  <span className="dash-analytics-lbl">Industries</span>
                  <span className="dash-analytics-db">PostgreSQL</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.total_deals || 0}</span>
                  <span className="dash-analytics-lbl">Total Deals</span>
                  <span className="dash-analytics-db">PostgreSQL</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{analytics.platform?.completed_deals || 0}</span>
                  <span className="dash-analytics-lbl">Deals Done</span>
                  <span className="dash-analytics-db">PostgreSQL</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">{Number(analytics.platform?.deals_waste_total || 0).toFixed(1)}t</span>
                  <span className="dash-analytics-lbl">Waste Traded</span>
                  <span className="dash-analytics-db">PostgreSQL</span>
                </div>
                <div className="dash-analytics-item">
                  <span className="dash-analytics-val">₹{Number(analytics.platform?.deals_value_total || 0).toLocaleString('en-IN')}</span>
                  <span className="dash-analytics-lbl">Deal Value</span>
                  <span className="dash-analytics-db">PostgreSQL</span>
                </div>
              </div>

              {/* Classification breakdown from Redis */}
              {analytics.platform?.classifications_by_type && Object.keys(analytics.platform.classifications_by_type).length > 0 && (
                <div className="dash-analytics-breakdown">
                  <h4>Classifications by Type</h4>
                  <div className="dash-breakdown-bars">
                    {Object.entries(analytics.platform.classifications_by_type)
                      .sort(([,a],[,b]) => b - a)
                      .map(([type, count]) => (
                        <div key={type} className="dash-bar-item">
                          <span className="dash-bar-label">{type}</span>
                          <div className="dash-bar-track">
                            <div className="dash-bar-fill" style={{
                              width: `${Math.min(100, (count / Math.max(...Object.values(analytics.platform.classifications_by_type))) * 100)}%`
                            }}></div>
                          </div>
                          <span className="dash-bar-count">{count}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
          {analyticsLoading && (
            <div className="dash-card">
              <p style={{textAlign:'center',color:'#888'}}>Loading analytics from 5 databases…</p>
            </div>
          )}

          {/* Bottom two-column: Recent Activity + Getting Started */}
          <div className="dash-bottom-grid">
            {/* Recent Activity (from MongoDB) */}
            <div className="dash-card">
              <h3>Recent Activity</h3>
              <div className="dash-activity">
                <div className="dash-activity-item">
                  <div className="dash-activity-dot"></div>
                  <div className="dash-activity-content">
                    <p>Account created</p>
                    <small>{joinDate}</small>
                  </div>
                </div>
                {analytics?.user?.recent_activity?.length > 0 ? (
                  analytics.user.recent_activity.slice(0, 8).map((a, i) => (
                    <div key={i} className="dash-activity-item">
                      <div className={`dash-activity-dot dot-${a.type}`}></div>
                      <div className="dash-activity-content">
                        <p>{a.type === 'match_search' ? `🔍 Searched matches for ${a.waste_type}` :
                            a.type === 'message_sent' ? `💬 Sent a message` :
                            a.type === 'classification' ? `📸 Classified waste` :
                            a.type}</p>
                        <small>{a.created_at ? new Date(a.created_at).toLocaleString('en-IN') : ''}</small>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="dash-activity-empty">
                    <p>Classify waste or create listings to see more activity here.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Getting Started */}
            <div className="dash-card">
              <h3>Getting Started</h3>
              <div className="dash-steps">
                <div className="dash-step">
                  <div className="dash-step-num">1</div>
                  <div className="dash-step-info">
                    <h4>Complete Your Profile</h4>
                    <p>Add location & contact for better matching.</p>
                    <Link to="/profile" className="dash-step-link">Go to Profile →</Link>
                  </div>
                </div>
                <div className="dash-step">
                  <div className="dash-step-num">2</div>
                  <div className="dash-step-info">
                    <h4>Classify Your Waste</h4>
                    <p>Upload an image — let AI identify it.</p>
                    <Link to="/classify" className="dash-step-link">Start Classifying →</Link>
                  </div>
                </div>
                <div className="dash-step">
                  <div className="dash-step-num">3</div>
                  <div className="dash-step-info">
                    <h4>Find Partners</h4>
                    <p>Connect with companies that need your waste.</p>
                    <Link to="/marketplace" className="dash-step-link">Browse Marketplace →</Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Dashboard;