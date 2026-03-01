import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
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
    (user.listings_count || 0) > 0 ||
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
              <div className="dash-stat-icon">🏷️</div>
              <div className="dash-stat-info">
                <span className="dash-stat-value">{user.listings_count || 0}</span>
                <span className="dash-stat-label">Listings</span>
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

          <div className="dash-grid">
            {/* Main column */}
            <div className="dash-main">
              {/* Quick Actions */}
              <div className="dash-card">
                <h3>Quick Actions</h3>
                <div className="dash-actions">
                  <Link to="/classify" className="dash-action-card">
                    <div className="dash-action-icon">📸</div>
                    <div className="dash-action-info">
                      <span className="dash-action-title">Classify Waste</span>
                      <span className="dash-action-desc">AI-powered waste identification</span>
                    </div>
                    <span className="dash-action-arrow">→</span>
                  </Link>
                  <Link to="/marketplace" className="dash-action-card">
                    <div className="dash-action-icon">🛒</div>
                    <div className="dash-action-info">
                      <span className="dash-action-title">Marketplace</span>
                      <span className="dash-action-desc">Browse & list waste materials</span>
                    </div>
                    <span className="dash-action-arrow">→</span>
                  </Link>
                  <Link to="/matches" className="dash-action-card">
                    <div className="dash-action-icon">🧠</div>
                    <div className="dash-action-info">
                      <span className="dash-action-title">AI Matching</span>
                      <span className="dash-action-desc">Find optimal waste partners</span>
                    </div>
                    <span className="dash-action-arrow">→</span>
                  </Link>
                  <Link to="/profile" className="dash-action-card">
                    <div className="dash-action-icon">👤</div>
                    <div className="dash-action-info">
                      <span className="dash-action-title">Profile</span>
                      <span className="dash-action-desc">Manage your company details</span>
                    </div>
                    <span className="dash-action-arrow">→</span>
                  </Link>
                </div>
              </div>

              {/* How You Can Contribute (merged from Impact) */}
              <div className="dash-card">
                <h3>How You Can Contribute</h3>
                <div className="dash-commitments">
                  <div className="dash-commitment">
                    <div className="dash-commitment-icon">📸</div>
                    <div>
                      <h4>Classify Your Waste</h4>
                      <p>Use AI to identify waste types and find the best recycling options.</p>
                    </div>
                  </div>
                  <div className="dash-commitment">
                    <div className="dash-commitment-icon">🏷️</div>
                    <div>
                      <h4>List on Marketplace</h4>
                      <p>Turn your waste into someone else's resource.</p>
                    </div>
                  </div>
                  <div className="dash-commitment">
                    <div className="dash-commitment-icon">🤝</div>
                    <div>
                      <h4>Connect with Partners</h4>
                      <p>Find businesses that can use your waste in their production.</p>
                    </div>
                  </div>
                  <div className="dash-commitment">
                    <div className="dash-commitment-icon">📊</div>
                    <div>
                      <h4>Track Your Progress</h4>
                      <p>Monitor impact as your contributions grow over time.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="dash-sidebar">
              {/* Company info card */}
              <div className="dash-card dash-profile-card">
                <div className="dash-profile-top">
                  <div className="dash-avatar">
                    {user.company_name ? user.company_name[0].toUpperCase() : 'U'}
                  </div>
                  <h4>{user.company_name || 'Your Company'}</h4>
                  <p className="dash-email">{user.email}</p>
                </div>
                <div className="dash-profile-details">
                  <div className="dash-detail-row">
                    <span className="dash-detail-label">Industry</span>
                    <span className="dash-detail-value">{user.industry_type || 'N/A'}</span>
                  </div>
                  <div className="dash-detail-row">
                    <span className="dash-detail-label">Location</span>
                    <span className="dash-detail-value">{user.location || 'Not set'}</span>
                  </div>
                  <div className="dash-detail-row">
                    <span className="dash-detail-label">Member Since</span>
                    <span className="dash-detail-value">{joinDate}</span>
                  </div>
                </div>
                <Link to="/profile" className="btn btn-outline btn-full">
                  Manage Profile
                </Link>
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

              {/* Recent Activity */}
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
                  <div className="dash-activity-empty">
                    <p>Classify waste or create listings to see more activity here.</p>
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