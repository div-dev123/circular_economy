import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../pages/Signup.css';

const Signup = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    companyName: '',
    industryType: '',
    location: '',
    phone: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Redirect if already logged in
  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        if (localStorage.getItem('isLoggedIn') === 'true') {
          navigate('/dashboard', { replace: true });
        }
      }
    } catch {
      // ignore
    }
  }, [navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Basic validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      setIsLoading(false);
      return;
    }

    try {
      const submitData = {
        email: formData.email,
        password: formData.password,
        company_name: formData.companyName,
        industry_type: formData.industryType,
        location: formData.location,
        phone: formData.phone
      };

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store user data and redirect
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('isLoggedIn', 'true');
        window.dispatchEvent(new Event('storage'));
        window.location.href = '/dashboard';
        return;
      } else {
        setError(data.error || 'Registration failed. Please try again.');
      }
    } catch (err) {
      setError('Cannot connect to server. Make sure the backend is running on port 5002.');
      console.error('Registration error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Indian industry types
  const indianIndustryTypes = [
    'Manufacturing',
    'Textiles',
    'Pharmaceuticals',
    'Automobile',
    'Chemicals',
    'Food Processing',
    'Metals & Mining',
    'Cement',
    'Paper & Pulp',
    'Leather',
    'Plastics',
    'Electronics',
    'IT Hardware',
    'Renewable Energy',
    'Construction',
    'Agriculture',
    'Phosphate',
    'Steel',
    'Aluminum',
    'Refinery',
    'Rubber',
    'Glass',
    'Ceramics'
  ];

  return (
    <div className="signup">
      <section className="signup-hero">
        <div className="container">
          <h1>Industry Registration</h1>
          <p className="subtitle">Join India's leading circular economy platform</p>
        </div>
      </section>

      <section className="signup-content">
        <div className="container">
          <div className="signup-form-container">
            <form className="signup-form" onSubmit={handleSubmit}>
              {error && <div className="error-message">{error}</div>}
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="companyName">Company Name *</label>
                  <input
                    type="text"
                    id="companyName"
                    name="companyName"
                    value={formData.companyName}
                    onChange={handleChange}
                    required
                    placeholder="Enter your company name"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="email">Business Email *</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    placeholder="Enter your business email"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="industryType">Industry Type *</label>
                  <select
                    id="industryType"
                    name="industryType"
                    value={formData.industryType}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select Industry Type</option>
                    {indianIndustryTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="location">Location (City/State) *</label>
                  <input
                    type="text"
                    id="location"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    required
                    placeholder="Enter city and state"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="phone">Phone Number</label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+91XXXXXXXXXX"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="password">Password *</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    placeholder="Create a password (min 6 chars)"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirm Password *</label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    placeholder="Confirm your password"
                  />
                </div>
              </div>

              <div className="form-group terms">
                <label>
                  <input type="checkbox" required /> I agree to the Terms of Service and Privacy Policy
                </label>
              </div>

              <button 
                type="submit" 
                className="btn btn-primary btn-large"
                disabled={isLoading}
              >
                {isLoading ? 'Registering...' : 'Register Now'}
              </button>
            </form>

            <div className="signup-links">
              <p>Already have an account? <a href="/login">Sign In</a></p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Signup;