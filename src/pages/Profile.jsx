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
          <div className="profile-card">
            {message && <div className="message">{message}</div>}

            <div className="profile-header">
              <div className="profile-avatar">
                <span>{user.company_name ? user.company_name[0].toUpperCase() : 'U'}</span>
              </div>
              <div className="profile-info">
                <h2>{user.company_name || user.email}</h2>
                <p className="email">{user.email}</p>
                <p className="industry">{user.industry_type}</p>
              </div>
            </div>

            <div className="profile-body">
              {!isEditing ? (
                <div className="profile-view">
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
                          ? new Date(user.created_at).toLocaleDateString()
                          : 'N/A'}
                      </p>
                    </div>
                  </div>

                  <div className="profile-actions">
                    <button
                      className="btn btn-primary"
                      onClick={() => setIsEditing(true)}
                    >
                      Edit Profile
                    </button>
                    <button
                      className="btn btn-outline"
                      onClick={handleLogout}
                    >
                      Logout
                    </button>
                  </div>
                </div>
              ) : (
                <div className="profile-edit">
                  <form className="edit-form">
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

          <div className="profile-sections">
            <div className="section-card">
              <h3>Account Statistics</h3>
              <div className="stats-grid">
                <div className="stat">
                  <div className="stat-value">0</div>
                  <div className="stat-label">Waste Classifications</div>
                </div>
                <div className="stat">
                  <div className="stat-value">0</div>
                  <div className="stat-label">Active Listings</div>
                </div>
                <div className="stat">
                  <div className="stat-value">0 tons</div>
                  <div className="stat-label">Total Waste Processed</div>
                </div>
                <div className="stat">
                  <div className="stat-value">0 tons CO₂</div>
                  <div className="stat-label">Environmental Impact</div>
                </div>
              </div>
            </div>

            <div className="section-card">
              <h3>Quick Actions</h3>
              <div className="actions-list">
                <a href="/classify" className="action-link">
                  <span className="action-icon">📸</span>
                  <span>Classify New Waste</span>
                </a>
                <a href="/marketplace" className="action-link">
                  <span className="action-icon">🏷️</span>
                  <span>View Marketplace</span>
                </a>
                <a href="/impact" className="action-link">
                  <span className="action-icon">📊</span>
                  <span>View Environmental Impact</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Profile;
