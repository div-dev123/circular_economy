import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import '../pages/Dashboard.css';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const userData = localStorage.getItem('user');
        if (userData) {
          const parsedUser = JSON.parse(userData);
          setUser(parsedUser);
        }
      }
    } catch (e) {
      // localStorage not available
    }
    setLoading(false);
  }, [navigate]);

  const handleLogout = () => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem('user');
        localStorage.removeItem('isLoggedIn');
      }
    } catch (e) {
      // localStorage not available, silently fail
    }
    navigate('/');
  };

  // Calculate join date from user data
  const joinDate = useMemo(() => {
    if (user) {
      return new Date(user.created_at || new Date()).toLocaleDateString();
    }
    return '';
  }, [user]);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="container">
          <h1>Welcome, {user.company_name || user.email}</h1>
          <div className="header-actions">
            <button className="btn btn-secondary" onClick={handleLogout}>Logout</button>
          </div>
        </div>
      </header>

      <section className="dashboard-hero">
        <div className="container">
          <h2>Industrial Symbiosis Platform</h2>
          <p className="subtitle">Transform waste into resources, connect with partners</p>
        </div>
      </section>

      <section className="dashboard-content">
        <div className="container">
          <div className="dashboard-grid">
            <div className="dashboard-card">
              <div className="card-icon">🏭</div>
              <h3>Your Industry</h3>
              <p>{user.industry_type}</p>
              <button 
                className="btn btn-outline"
                onClick={() => navigate('/profile')}
              >
                Manage Profile
              </button>
            </div>

            <div className="dashboard-card">
              <div className="card-icon">📸</div>
              <h3>Classify Waste</h3>
              <p>Upload images for AI-powered identification</p>
              <button 
                className="btn btn-primary"
                onClick={() => navigate('/classify')}
              >
                Classify Now
              </button>
            </div>

            <div className="dashboard-card">
              <div className="card-icon">🛒</div>
              <h3>Marketplace</h3>
              <p>Browse and list waste materials</p>
              <button 
                className="btn btn-outline"
                onClick={() => navigate('/marketplace')}
              >
                View Marketplace
              </button>
            </div>

            <div className="dashboard-card">
              <div className="card-icon">📊</div>
              <h3>Impact Dashboard</h3>
              <p>Track your environmental contributions</p>
              <button 
                className="btn btn-outline"
                onClick={() => navigate('/impact')}
              >
                View Impact
              </button>
            </div>
          </div>

          <div className="dashboard-section">
            <h2>Recent Activity</h2>
            <div className="activity-feed">
              <div className="activity-item">
                <div className="activity-icon">🆕</div>
                <div className="activity-content">
                  <h4>Account Created</h4>
                  <p>Welcome to the Industrial Symbiosis Platform!</p>
                  <small>Joined on {joinDate}</small>
                </div>
              </div>
              {/* More activity items would be dynamically loaded */}
            </div>
          </div>

          <div className="dashboard-section">
            <h2>Quick Actions</h2>
            <div className="quick-actions">
              <button 
                className="action-btn"
                onClick={() => navigate('/classify')}
              >
                <div className="action-icon">📷</div>
                <span>Classify New Waste</span>
              </button>
              <button 
                className="action-btn"
                onClick={() => navigate('/marketplace')}
              >
                <div className="action-icon">🏷️</div>
                <span>Create Listing</span>
              </button>
              <button 
                className="action-btn"
                onClick={() => navigate('/search')}
              >
                <div className="action-icon">🔍</div>
                <span>Find Materials</span>
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Dashboard;