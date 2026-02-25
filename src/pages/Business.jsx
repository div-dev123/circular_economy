import React from 'react';
import './Business.css';

const Business = () => {
  return (
    <div className="business">
      <section className="business-hero">
        <div className="container">
          <h1>Business Solutions</h1>
          <p className="subtitle">Enterprise-grade tools for sustainable waste management</p>
        </div>
      </section>

      <section className="solutions-section">
        <div className="container">
          <div className="solutions-grid">
            <div className="solution-card">
              <div className="solution-icon">🏢</div>
              <h3>Enterprise Platform</h3>
              <p>Comprehensive waste management solution for large organizations with multiple facilities</p>
              <ul>
                <li>Multi-site management</li>
                <li>Custom compliance reporting</li>
                <li>API integration capabilities</li>
                <li>Dedicated support team</li>
              </ul>
              <button className="btn btn-primary">Learn More</button>
            </div>
            
            <div className="solution-card">
              <div className="solution-icon">🏭</div>
              <h3>Industrial Symbiosis</h3>
              <p>Connect with partners to create circular supply chains and reduce waste costs</p>
              <ul>
                <li>Smart partner matching</li>
                <li>Supply chain optimization</li>
                <li>Cost-benefit analysis</li>
                <li>Impact tracking</li>
              </ul>
              <button className="btn btn-primary">Learn More</button>
            </div>
            
            <div className="solution-card">
              <div className="solution-icon">📊</div>
              <h3>Analytics Suite</h3>
              <p>Data-driven insights for sustainability reporting and decision making</p>
              <ul>
                <li>Real-time impact metrics</li>
                <li>ROI calculations</li>
                <li>Compliance dashboards</li>
                <li>Custom reporting</li>
              </ul>
              <button className="btn btn-primary">Learn More</button>
            </div>
          </div>
        </div>
      </section>

      <section className="industries-section">
        <div className="container">
          <div className="section-header">
            <h2>Industries We Serve</h2>
            <p>Tailored solutions for specific industry challenges</p>
          </div>
          
          <div className="industries-grid">
            <div className="industry-card">
              <div className="industry-icon">👕</div>
              <h3>Textile & Apparel</h3>
              <p>Fabric scraps, dye waste, and production by-products</p>
              <div className="industry-stats">
                <div className="stat">
                  <span className="stat-value">70%</span>
                  <span className="stat-label">Waste Reduction</span>
                </div>
              </div>
            </div>
            
            <div className="industry-card">
              <div className="industry-icon">🔧</div>
              <h3>Manufacturing</h3>
              <p>Metal shavings, plastic waste, and production materials</p>
              <div className="industry-stats">
                <div className="stat">
                  <span className="stat-value">85%</span>
                  <span className="stat-label">Cost Savings</span>
                </div>
              </div>
            </div>
            
            <div className="industry-card">
              <div className="industry-icon">🍎</div>
              <h3>Food & Agriculture</h3>
              <p>Organic waste, packaging materials, and by-products</p>
              <div className="industry-stats">
                <div className="stat">
                  <span className="stat-value">90%</span>
                  <span className="stat-label">Diversion Rate</span>
                </div>
              </div>
            </div>
            
            <div className="industry-card">
              <div className="industry-icon">🏗️</div>
              <h3>Construction</h3>
              <p>Building materials, concrete, and demolition waste</p>
              <div className="industry-stats">
                <div className="stat">
                  <span className="stat-value">75%</span>
                  <span className="stat-label">Material Recovery</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="features-section">
        <div className="container">
          <div className="features-content">
            <div className="features-text">
              <h2>Key Features</h2>
              <div className="features-list">
                <div className="feature-item">
                  <div className="feature-icon">🔒</div>
                  <div className="feature-content">
                    <h4>Enterprise Security</h4>
                    <p>Bank-level encryption and compliance with industry standards</p>
                  </div>
                </div>
                
                <div className="feature-item">
                  <div className="feature-icon">🔄</div>
                  <div className="feature-content">
                    <h4>Automated Workflows</h4>
                    <p>Streamlined processes from waste identification to partner matching</p>
                  </div>
                </div>
                
                <div className="feature-item">
                  <div className="feature-icon">📱</div>
                  <div className="feature-content">
                    <h4>Mobile Access</h4>
                    <p>Manage your waste operations from anywhere with our mobile app</p>
                  </div>
                </div>
                
                <div className="feature-item">
                  <div className="feature-icon">📈</div>
                  <div className="feature-content">
                    <h4>Advanced Analytics</h4>
                    <p>Detailed reporting on environmental impact and financial benefits</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="features-visual">
              <div className="dashboard-mockup">
                <div className="dashboard-header">
                  <h4>Business Dashboard</h4>
                  <div className="dashboard-controls">
                    <span className="control">📊</span>
                    <span className="control">📅</span>
                    <span className="control">⚙️</span>
                  </div>
                </div>
                <div className="dashboard-content">
                  <div className="metric-card">
                    <div className="metric-value">1.2M tons</div>
                    <div className="metric-label">Waste Diverted</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-value">$2.4M</div>
                    <div className="metric-label">Cost Savings</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-value">84%</div>
                    <div className="metric-label">Reduction Rate</div>
                  </div>
                </div>
                <div className="chart-placeholder">
                  <div className="chart-title">Monthly Waste Diversion</div>
                  <div className="chart-bars">
                    <div className="chart-bar" style={{height: '60%'}}></div>
                    <div className="chart-bar" style={{height: '75%'}}></div>
                    <div className="chart-bar" style={{height: '85%'}}></div>
                    <div className="chart-bar" style={{height: '90%'}}></div>
                    <div className="chart-bar" style={{height: '88%'}}></div>
                    <div className="chart-bar" style={{height: '92%'}}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="pricing-section">
        <div className="container">
          <div className="section-header">
            <h2>Flexible Pricing Plans</h2>
            <p>Choose the plan that fits your business needs</p>
          </div>
          
          <div className="pricing-grid">
            <div className="pricing-card">
              <div className="plan-name">Starter</div>
              <div className="plan-price">
                <span className="amount">$299</span>
                <span className="period">/month</span>
              </div>
              <ul className="plan-features">
                <li>Up to 100 waste listings</li>
                <li>Basic analytics</li>
                <li>Email support</li>
                <li>Standard compliance reports</li>
              </ul>
              <button className="btn btn-secondary">Get Started</button>
            </div>
            
            <div className="pricing-card popular">
              <div className="popular-badge">Most Popular</div>
              <div className="plan-name">Professional</div>
              <div className="plan-price">
                <span className="amount">$799</span>
                <span className="period">/month</span>
              </div>
              <ul className="plan-features">
                <li>Unlimited waste listings</li>
                <li>Advanced analytics</li>
                <li>Priority support</li>
                <li>Custom reporting</li>
                <li>API access</li>
                <li>Multi-user accounts</li>
              </ul>
              <button className="btn btn-primary">Get Started</button>
            </div>
            
            <div className="pricing-card">
              <div className="plan-name">Enterprise</div>
              <div className="plan-price">
                <span className="amount">Custom</span>
              </div>
              <ul className="plan-features">
                <li>Everything in Professional</li>
                <li>Dedicated account manager</li>
                <li>Custom integrations</li>
                <li>On-premise deployment</li>
                <li>Training & onboarding</li>
                <li>SLA guarantee</li>
              </ul>
              <button className="btn btn-secondary">Contact Sales</button>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Transform Your Waste Management?</h2>
            <p>Join leading companies in building sustainable supply chains</p>
            <div className="cta-buttons">
              <button className="btn btn-primary btn-large">Schedule Demo</button>
              <button className="btn btn-secondary btn-large">Contact Sales</button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Business;