import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Profile.css';

const Profile = () => {
  const [user, setUser] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const userData = localStorage.getItem('user');
        if (userData) {
          const parsedUser = JSON.parse(userData);
          setUser(parsedUser);
          setFormData(parsedUser);
        } else {
          navigate('/login');
        }
      } else {
        navigate('/login');
      }
    } catch {
      navigate('/login');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSaveProfile = async () => {
    try {
      const response = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setUser(data.user);
        try {
          if (typeof window !== 'undefined' && window.localStorage) {
            localStorage.setItem('user', JSON.stringify(data.user));
          }
        } catch {
          // localStorage not available
        }
        setIsEditing(false);
        setMessage('Profile updated successfully!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        setMessage(data.error || 'Failed to update profile');
      }
    } catch (err) {
      setMessage('Network error. Please try again.');
      console.error('Profile update error:', err);
    }
  };

  const handleLogout = () => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem('user');
        localStorage.removeItem('isLoggedIn');
      }
    } catch {
      // localStorage not available
    }
    navigate('/login');
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return (
    <div className="profile">
      <section className="profile-hero">
        <div className="container">
          <h1>My Profile</h1>
          <p className="subtitle">Manage your account and company information</p>
        </div>
      </section>

      <section className="profile-content">
        <div className="container">
          {message && <div className="message">{message}</div>}

          <div className="profile-layout">
            {/* Left sidebar */}
            <div className="profile-sidebar">
              <div className="profile-card">
                <div className="profile-header">
                  <div className="profile-avatar">
                    <span>{user.company_name ? user.company_name[0].toUpperCase() : 'U'}</span>
                  </div>
                  <h2>{user.company_name || user.email}</h2>
                  <p className="email">{user.email}</p>
                  <span className="industry-badge">{user.industry_type || 'N/A'}</span>
                  {user.location && <p className="location">📍 {user.location}</p>}
                </div>

                <div className="sidebar-stats">
                  <div className="sidebar-stat">
                    <span className="sidebar-stat-value">{user.classifications_count || 0}</span>
                    <span className="sidebar-stat-label">Classifications</span>
                  </div>
                  <div className="sidebar-stat">
                    <span className="sidebar-stat-value">{user.listings_count || 0}</span>
                    <span className="sidebar-stat-label">Listings</span>
                  </div>
                  <div className="sidebar-stat">
                    <span className="sidebar-stat-value">{Number(user.co2_saved_tons || 0).toFixed(1)}</span>
                    <span className="sidebar-stat-label">CO₂ Saved (t)</span>
                  </div>
                </div>

                <div className="sidebar-actions">
                  <button className="btn btn-primary btn-full" onClick={() => setIsEditing(true)}>
                    ✏️ Edit Profile
                  </button>
                  <button className="btn btn-outline btn-full" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              </div>
            </div>

            {/* Main content */}
            <div className="profile-main">
              {!isEditing ? (
                <>
                  {/* Info Card */}
                  <div className="section-card">
                    <h3>Company Information</h3>
                    <div className="info-grid">
                      <div className="info-item">
                        <label>Company Name</label>
                        <p>{user.company_name || 'N/A'}</p>
                      </div>
                      <div className="info-item">
                        <label>Email</label>
                        <p>{user.email}</p>
                      </div>
                      <div className="info-item">
                        <label>Industry Type</label>
                        <p>{user.industry_type || 'N/A'}</p>
                      </div>
                      <div className="info-item">
                        <label>Location</label>
                        <p>{user.location || 'N/A'}</p>
                      </div>
                      <div className="info-item">
                        <label>Phone</label>
                        <p>{user.phone || 'N/A'}</p>
                      </div>
                      <div className="info-item">
                        <label>Member Since</label>
                        <p>
                          {user.created_at
                            ? new Date(user.created_at).toLocaleDateString('en-IN', {
                                year: 'numeric', month: 'long', day: 'numeric'
                              })
                            : 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Stats Cards Row */}
                  <div className="stats-row">
                    <div className="stat-card">
                      <div className="stat-icon">📸</div>
                      <div className="stat-value">{user.classifications_count || 0}</div>
                      <div className="stat-label">Waste Classifications</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-icon">🏷️</div>
                      <div className="stat-value">{user.listings_count || 0}</div>
                      <div className="stat-label">Active Listings</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-icon">⚖️</div>
                      <div className="stat-value">{Number(user.waste_processed_tons || 0).toFixed(1)}t</div>
                      <div className="stat-label">Waste Processed</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-icon">🌍</div>
                      <div className="stat-value">{Number(user.co2_saved_tons || 0).toFixed(1)}t</div>
                      <div className="stat-label">CO₂ Saved</div>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="section-card">
                    <h3>Quick Actions</h3>
                    <div className="actions-grid">
                      <a href="/classify" className="action-card">
                        <span className="action-icon">📸</span>
                        <span className="action-text">Classify Waste</span>
                      </a>
                      <a href="/marketplace" className="action-card">
                        <span className="action-icon">🏷️</span>
                        <span className="action-text">Marketplace</span>
                      </a>
                      <a href="/impact" className="action-card">
                        <span className="action-icon">📊</span>
                        <span className="action-text">My Impact</span>
                      </a>
                      <a href="/dashboard" className="action-card">
                        <span className="action-icon">📈</span>
                        <span className="action-text">Dashboard</span>
                      </a>
                    </div>
                  </div>
                </>
              ) : (
                <div className="section-card">
                  <h3>Edit Profile</h3>
                  <form className="edit-form">
                    <div className="form-row">
                      <div className="form-group">
                        <label>Company Name</label>
                        <input
                          type="text"
                          name="company_name"
                          value={formData.company_name || ''}
                          onChange={handleInputChange}
                        />
                      </div>
                      <div className="form-group">
                        <label>Email</label>
                        <input
                          type="email"
                          name="email"
                          value={formData.email || ''}
                          disabled
                        />
                      </div>
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label>Industry Type</label>
                        <input
                          type="text"
                          name="industry_type"
                          value={formData.industry_type || ''}
                          onChange={handleInputChange}
                        />
                      </div>
                      <div className="form-group">
                        <label>Location</label>
                        <input
                          type="text"
                          name="location"
                          value={formData.location || ''}
                          onChange={handleInputChange}
                          placeholder="City, State"
                        />
                      </div>
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label>Phone</label>
                        <input
                          type="tel"
                          name="phone"
                          value={formData.phone || ''}
                          onChange={handleInputChange}
                          placeholder="+91XXXXXXXXXX"
                        />
                      </div>
                    </div>

                    <div className="form-actions">
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={handleSaveProfile}
                      >
                        Save Changes
                      </button>
                      <button
                        type="button"
                        className="btn btn-outline"
                        onClick={() => {
                          setIsEditing(false);
                          setFormData(user);
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Profile;
