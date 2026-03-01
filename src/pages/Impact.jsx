import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Impact.css';

const Impact = () => {
  const [userStats, setUserStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Load user stats from localStorage (synced from backend)
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const userData = JSON.parse(localStorage.getItem('user') || '{}');
        if (userData && userData.id) {
          setUserStats({
            classifications: userData.classifications_count || 0,
            listings: userData.listings_count || 0,
            waste_processed: parseFloat(userData.waste_processed_tons || 0).toFixed(2),
            co2_saved: parseFloat(userData.co2_saved_tons || 0).toFixed(2),
            cost_savings: parseFloat(userData.cost_savings || 0).toFixed(2),
          });
        }
      }
    } catch {
      // localStorage not available
    }
    setLoading(false);
  }, []);

  const hasActivity = userStats && (
    userStats.classifications > 0 ||
    userStats.listings > 0 ||
    parseFloat(userStats.waste_processed) > 0
  );

  if (loading) {
    return <div className="loading">Loading your impact data...</div>;
  }

  return (
    <div className="impact">
      <section className="impact-hero">
        <div className="container">
          <h1>Your Impact Dashboard</h1>
          <p className="subtitle">Track your environmental and economic contributions</p>
        </div>
      </section>

      <section className="metrics-section">
        <div className="container">
          <div className="metrics-grid">
            <div className="metric-card primary">
              <div className="metric-icon">📊</div>
              <div className="metric-content">
                <div className="metric-value">{userStats?.classifications || 0}</div>
                <div className="metric-label">Waste Classifications</div>
              </div>
            </div>

            <div className="metric-card primary">
              <div className="metric-icon">🏷️</div>
              <div className="metric-content">
                <div className="metric-value">{userStats?.listings || 0}</div>
                <div className="metric-label">Marketplace Listings</div>
              </div>
            </div>

            <div className="metric-card secondary">
              <div className="metric-icon">🗑️</div>
              <div className="metric-content">
                <div className="metric-value">{userStats?.waste_processed || '0.00'} tons</div>
                <div className="metric-label">Waste Processed</div>
              </div>
            </div>

            <div className="metric-card secondary">
              <div className="metric-icon">🌍</div>
              <div className="metric-content">
                <div className="metric-value">{userStats?.co2_saved || '0.00'} tons</div>
                <div className="metric-label">CO₂ Saved</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {!hasActivity ? (
        <section className="empty-activity-section">
          <div className="container">
            <div className="empty-activity">
              <div className="empty-icon">🌱</div>
              <h2>Start Making an Impact</h2>
              <p>You haven't recorded any activity yet. Begin by classifying waste or creating a marketplace listing to start tracking your environmental contributions.</p>
              <div className="empty-actions">
                <button className="btn btn-primary" onClick={() => navigate('/classify')}>
                  Classify Waste
                </button>
                <button className="btn btn-outline" onClick={() => navigate('/marketplace')}>
                  View Marketplace
                </button>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <section className="activity-section">
          <div className="container">
            <div className="section-header">
              <h2>Your Activity Summary</h2>
              <p>Your contributions to the circular economy</p>
            </div>
            <div className="activity-summary">
              <div className="summary-card">
                <h3>💰 Cost Savings</h3>
                <p className="summary-value">₹{userStats?.cost_savings || '0.00'}</p>
                <p className="summary-desc">Estimated savings from waste diversion</p>
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="sustainability-section">
        <div className="container">
          <div className="section-header">
            <h2>How You Can Contribute</h2>
            <p>Every action counts towards building a sustainable future</p>
          </div>

          <div className="commitments-grid">
            <div className="commitment">
              <div className="commitment-icon">📸</div>
              <div className="commitment-content">
                <h4>Classify Your Waste</h4>
                <p>Use AI-powered classification to identify waste types and find the best recycling options</p>
              </div>
            </div>

            <div className="commitment">
              <div className="commitment-icon">🏷️</div>
              <div className="commitment-content">
                <h4>List on Marketplace</h4>
                <p>Turn your waste into someone else's resource by listing materials on the marketplace</p>
              </div>
            </div>

            <div className="commitment">
              <div className="commitment-icon">🤝</div>
              <div className="commitment-content">
                <h4>Connect with Partners</h4>
                <p>Find businesses that can use your waste materials in their production processes</p>
              </div>
            </div>

            <div className="commitment">
              <div className="commitment-icon">📊</div>
              <div className="commitment-content">
                <h4>Track Your Progress</h4>
                <p>Monitor your environmental impact and see how your contributions grow over time</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Make a Difference?</h2>
            <p>Every piece of waste classified and diverted brings us closer to a circular economy</p>
            <div className="cta-buttons">
              <button className="btn btn-primary btn-large" onClick={() => navigate('/classify')}>
                Start Classifying
              </button>
              <button className="btn btn-secondary btn-large" onClick={() => navigate('/marketplace')}>
                Browse Marketplace
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Impact;
