import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h1 className="hero-title">
              Transforming Waste into <span className="highlight">Opportunity</span>
            </h1>
            <p className="hero-subtitle">
              The world's first AI-powered B2B marketplace for industrial symbiosis. 
              Connect waste producers with innovative solutions and build a sustainable future.
            </p>
            <div className="hero-buttons">
              <Link to="/marketplace" className="btn btn-primary btn-large">
                Explore Marketplace
              </Link>
              <Link to="/how-it-works" className="btn btn-secondary btn-large">
                How It Works
              </Link>
            </div>
            <div className="hero-stats">
              <div className="stat">
                <span className="stat-number">10M+</span>
                <span className="stat-label">Tons Waste Diverted</span>
              </div>
              <div className="stat">
                <span className="stat-number">500+</span>
                <span className="stat-label">Business Partners</span>
              </div>
              <div className="stat">
                <span className="stat-number">2.3B</span>
                <span className="stat-label">CO₂ Saved (tons)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="problem-section">
        <div className="container">
          <div className="section-header">
            <h2>The Waste Crisis</h2>
            <p>Industrial and municipal waste causes severe environmental damage when mismanaged</p>
          </div>
          <div className="problem-grid">
            <div className="problem-card">
              <div className="problem-icon">🔥</div>
              <h3>Climate Impact</h3>
              <p>Landfills contribute ~10% of human-caused methane emissions, accelerating climate change</p>
            </div>
            <div className="problem-card">
              <div className="problem-icon">💧</div>
              <h3>Water Pollution</h3>
              <p>Toxic chemicals leach from landfills into groundwater, contaminating drinking water</p>
            </div>
            <div className="problem-card">
              <div className="problem-icon">🌍</div>
              <h3>Resource Depletion</h3>
              <p>Virgin material extraction destroys habitats and biodiversity at an alarming rate</p>
            </div>
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section className="solution-section">
        <div className="container">
          <div className="solution-content">
            <div className="solution-text">
              <h2>The Circular Economy Solution</h2>
              <p>
                Our platform bridges the gap between waste producers and innovative solutions through 
                AI-powered classification, intelligent matching, and end-to-end circular flow management.
              </p>
              <div className="solution-features">
                <div className="feature">
                  <span className="feature-icon">🤖</span>
                  <div>
                    <h4>AI Waste Classification</h4>
                    <p>Instant multi-label identification using advanced computer vision</p>
                  </div>
                </div>
                <div className="feature">
                  <span className="feature-icon">🤝</span>
                  <div>
                    <h4>Smart Matching</h4>
                    <p>Connect producers to buyers based on type, quantity, location, and compliance</p>
                  </div>
                </div>
                <div className="feature">
                  <span className="feature-icon">📊</span>
                  <div>
                    <h4>Impact Analytics</h4>
                    <p>Real-time tracking of CO₂ saved, landfill diversion, and cost savings</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="solution-image">
              <div className="circular-diagram">
                <div className="circle-item">Reduce</div>
                <div className="circle-item">Reuse</div>
                <div className="circle-item">Recycle</div>
                <div className="center-text">Circular Flow</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Join the Circular Revolution?</h2>
            <p>Start transforming your waste into valuable resources today</p>
            <div className="cta-buttons">
              <Link to="/business" className="btn btn-primary btn-large">
                For Businesses
              </Link>
              <Link to="/classify" className="btn btn-secondary btn-large">
                Try Waste Classification
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;