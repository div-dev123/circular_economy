import React from 'react';
import './HowItWorks.css';

const HowItWorks = () => {
  return (
    <div className="how-it-works">
      <section className="hero-section">
        <div className="container">
          <h1>How Our Platform Works</h1>
          <p className="subtitle">Transforming waste management through AI-powered innovation</p>
        </div>
      </section>

      <section className="process-section">
        <div className="container">
          <div className="process-steps">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Upload Waste Image</h3>
                <p>Simply take a photo of your industrial waste or upload an existing image to our platform</p>
                <div className="step-features">
                  <span className="feature-tag">📱 Mobile Friendly</span>
                  <span className="feature-tag">📸 Instant Upload</span>
                  <span className="feature-tag">🔒 Secure Processing</span>
                </div>
              </div>
            </div>
            
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>AI Classification</h3>
                <p>Our advanced computer vision system instantly identifies waste type, composition, and potential value</p>
                <div className="step-features">
                  <span className="feature-tag">🤖 AI-Powered</span>
                  <span className="feature-tag">🔍 Multi-Label</span>
                  <span className="feature-tag">⚡ Real-time</span>
                </div>
              </div>
            </div>
            
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Smart Matching</h3>
                <p>We connect you with the perfect partners based on waste type, quantity, location, and compliance requirements</p>
                <div className="step-features">
                  <span className="feature-tag">🤝 Intelligent</span>
                  <span className="feature-tag">📍 Location-Based</span>
                  <span className="feature-tag">✅ Compliant</span>
                </div>
              </div>
            </div>
            
            <div className="step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h3>Complete Transaction</h3>
                <p>Negotiate terms, arrange logistics, and track the entire circular flow process</p>
                <div className="step-features">
                  <span className="feature-tag">💬 Negotiation</span>
                  <span className="feature-tag">🚛 Logistics</span>
                  <span className="feature-tag">📊 Tracking</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="technology-section">
        <div className="container">
          <div className="section-header">
            <h2>Advanced Technology Stack</h2>
            <p>Powered by cutting-edge AI and machine learning</p>
          </div>
          
          <div className="tech-grid">
            <div className="tech-card">
              <div className="tech-icon">🧠</div>
              <h3>Computer Vision</h3>
              <p>Convolutional Neural Networks for accurate waste classification using transfer learning</p>
            </div>
            
            <div className="tech-card">
              <div className="tech-icon">🔗</div>
              <h3>Matching Algorithms</h3>
              <p>Hybrid rule-based and machine learning systems for optimal partner connections</p>
            </div>
            
            <div className="tech-card">
              <div className="tech-icon">📊</div>
              <h3>Analytics Engine</h3>
              <p>Real-time impact tracking and performance metrics for all circular flows</p>
            </div>
            
            <div className="tech-card">
              <div className="tech-icon">🔒</div>
              <h3>Security Framework</h3>
              <p>Enterprise-grade security with data encryption and compliance certifications</p>
            </div>
          </div>
        </div>
      </section>

      <section className="benefits-section">
        <div className="container">
          <div className="benefits-content">
            <div className="benefits-text">
              <h2>Why Choose Our Platform?</h2>
              <div className="benefits-list">
                <div className="benefit-item">
                  <div className="benefit-icon">⚡</div>
                  <div className="benefit-content">
                    <h4>Lightning Fast</h4>
                    <p>Get instant waste classification and partner matching in seconds</p>
                  </div>
                </div>
                
                <div className="benefit-item">
                  <div className="benefit-icon">🌍</div>
                  <div className="benefit-content">
                    <h4>Globally Scalable</h4>
                    <p>Works across industries and regions with localized compliance</p>
                  </div>
                </div>
                
                <div className="benefit-item">
                  <div className="benefit-icon">💰</div>
                  <div className="benefit-content">
                    <h4>Cost Effective</h4>
                    <p>Eliminate expensive hardware and manual classification processes</p>
                  </div>
                </div>
                
                <div className="benefit-item">
                  <div className="benefit-icon">📈</div>
                  <div className="benefit-content">
                    <h4>Measurable Impact</h4>
                    <p>Track CO₂ savings, landfill diversion, and ROI in real-time</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="benefits-visual">
              <div className="dashboard-preview">
                <div className="dashboard-header">
                  <h4>Impact Dashboard</h4>
                </div>
                <div className="dashboard-stats">
                  <div className="stat-card">
                    <span className="stat-value">1.2M</span>
                    <span className="stat-label">Tonnes Diverted</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">84%</span>
                    <span className="stat-label">Cost Savings</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">2.1B</span>
                    <span className="stat-label">CO₂ Avoided</span>
                  </div>
                </div>
                <div className="chart-placeholder">
                  <div className="chart-bar" style={{height: '60%'}}></div>
                  <div className="chart-bar" style={{height: '80%'}}></div>
                  <div className="chart-bar" style={{height: '45%'}}></div>
                  <div className="chart-bar" style={{height: '75%'}}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Get Started?</h2>
            <p>Join thousands of businesses transforming waste into opportunity</p>
            <div className="cta-buttons">
              <button className="btn btn-primary btn-large">Create Free Account</button>
              <button className="btn btn-secondary btn-large">Schedule Demo</button>
            </div>
          </div>
        </div>
      </section>

      <section className="india-focus-section">
        <div className="container">
          <div className="section-header">
            <h2>Leading Circular Economy in India</h2>
            <p>Supporting India's transition to sustainable industrial practices</p>
          </div>
          
          <div className="india-benefits-grid">
            <div className="india-benefit-card">
              <div className="benefit-icon">🏭</div>
              <h3>MSME Support</h3>
              <p>Tailored solutions for India's Micro, Small & Medium Enterprises</p>
            </div>
            
            <div className="india-benefit-card">
              <div className="benefit-icon">🌍</div>
              <h3>Swarachna Initiative</h3>
              <p>Align with India's self-reliance mission through waste valorization</p>
            </div>
            
            <div className="india-benefit-card">
              <div className="benefit-icon">📊</div>
              <h3>Government Compliance</h3>
              <p>Integrated with CPCB and state pollution control board requirements</p>
            </div>
            
            <div className="india-benefit-card">
              <div className="benefit-icon">💰</div>
              <h3>Subsidy Opportunities</h3>
              <p>Access government incentives for waste-to-resource initiatives</p>
            </div>
          </div>
          
          <div className="india-statistics">
            <div className="stat-item">
              <span className="stat-number">₹2.5L Cr</span>
              <span className="stat-label">Potential market opportunity in India</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">300M</span>
              <span className="stat-label">Tonnes of waste generated annually</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">60%</span>
              <span className="stat-label">Waste that can be recycled/valorized</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HowItWorks;