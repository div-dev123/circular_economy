import React from 'react';
import './Impact.css';

const Impact = () => {
  return (
    <div className="impact">
      <section className="impact-hero">
        <div className="container">
          <h1>Impact Dashboard</h1>
          <p className="subtitle">Real-time tracking of environmental and economic benefits</p>
        </div>
      </section>

      <section className="metrics-section">
        <div className="container">
          <div className="metrics-grid">
            <div className="metric-card primary">
              <div className="metric-icon">🌍</div>
              <div className="metric-content">
                <div className="metric-value">2.3B</div>
                <div className="metric-label">Tons CO₂ Saved</div>
                <div className="metric-trend positive">+12% from last month</div>
              </div>
            </div>
            
            <div className="metric-card primary">
              <div className="metric-icon">🗑️</div>
              <div className="metric-content">
                <div className="metric-value">10M+</div>
                <div className="metric-label">Tons Waste Diverted</div>
                <div className="metric-trend positive">+8% from last month</div>
              </div>
            </div>
            
            <div className="metric-card secondary">
              <div className="metric-icon">💰</div>
              <div className="metric-content">
                <div className="metric-value">$1.8B</div>
                <div className="metric-label">Cost Savings Generated</div>
                <div className="metric-trend positive">+15% from last month</div>
              </div>
            </div>
            
            <div className="metric-card secondary">
              <div className="metric-icon">🏭</div>
              <div className="metric-content">
                <div className="metric-value">500+</div>
                <div className="metric-label">Business Partners</div>
                <div className="metric-trend positive">+25 new this month</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="charts-section">
        <div className="container">
          <div className="section-header">
            <h2>Environmental Impact Over Time</h2>
            <p>Detailed analytics showing our collective progress</p>
          </div>
          
          <div className="charts-grid">
            <div className="chart-card">
              <div className="chart-header">
                <h3>Monthly CO₂ Reduction</h3>
                <div className="chart-controls">
                  <button className="time-filter active">6M</button>
                  <button className="time-filter">1Y</button>
                  <button className="time-filter">All</button>
                </div>
              </div>
              <div className="chart-container">
                <div className="line-chart">
                  <div className="chart-grid"></div>
                  <div className="chart-line" style={{height: '200px'}}>
                    <div className="data-point" style={{left: '10%', bottom: '30%'}}></div>
                    <div className="data-point" style={{left: '25%', bottom: '45%'}}></div>
                    <div className="data-point" style={{left: '40%', bottom: '55%'}}></div>
                    <div className="data-point" style={{left: '55%', bottom: '65%'}}></div>
                    <div className="data-point" style={{left: '70%', bottom: '75%'}}></div>
                    <div className="data-point" style={{left: '85%', bottom: '80%'}}></div>
                  </div>
                </div>
                <div className="chart-stats">
                  <div className="stat">
                    <span className="stat-label">Current Rate</span>
                    <span className="stat-value">38M tons/month</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Target</span>
                    <span className="stat-value">50M tons/month</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="chart-card">
              <div className="chart-header">
                <h3>Waste Type Distribution</h3>
              </div>
              <div className="chart-container">
                <div className="pie-chart">
                  <div className="pie-slice" style={{background: 'conic-gradient(#2d5a3d 0% 40%, #3a7d44 40% 65%, #1a2e1f 65% 85%, #a8d5ba 85% 100%)'}}></div>
                  <div className="pie-center">
                    <div className="center-value">100%</div>
                    <div className="center-label">Total Diverted</div>
                  </div>
                </div>
                <div className="chart-legend">
                  <div className="legend-item">
                    <div className="legend-color" style={{backgroundColor: '#2d5a3d'}}></div>
                    <div className="legend-text">
                      <span className="legend-label">Plastic</span>
                      <span className="legend-percent">40%</span>
                    </div>
                  </div>
                  <div className="legend-item">
                    <div className="legend-color" style={{backgroundColor: '#3a7d44'}}></div>
                    <div className="legend-text">
                      <span className="legend-label">Metal</span>
                      <span className="legend-percent">25%</span>
                    </div>
                  </div>
                  <div className="legend-item">
                    <div className="legend-color" style={{backgroundColor: '#1a2e1f'}}></div>
                    <div className="legend-text">
                      <span className="legend-label">Organic</span>
                      <span className="legend-percent">20%</span>
                    </div>
                  </div>
                  <div className="legend-item">
                    <div className="legend-color" style={{backgroundColor: '#a8d5ba'}}></div>
                    <div className="legend-text">
                      <span className="legend-label">Other</span>
                      <span className="legend-percent">15%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="regional-section">
        <div className="container">
          <div className="section-header">
            <h2>Regional Impact</h2>
            <p>See how different regions are contributing to the circular economy</p>
          </div>
          
          <div className="regional-grid">
            <div className="region-card">
              <div className="region-header">
                <h3>North America</h3>
                <div className="region-flag">🇺🇸</div>
              </div>
              <div className="region-stats">
                <div className="stat-item">
                  <span className="stat-icon">🏭</span>
                  <div className="stat-content">
                    <span className="stat-value">150+</span>
                    <span className="stat-label">Facilities</span>
                  </div>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">🌍</span>
                  <div className="stat-content">
                    <span className="stat-value">850M</span>
                    <span className="stat-label">Tons CO₂ Saved</span>
                  </div>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">💰</span>
                  <div className="stat-content">
                    <span className="stat-value">$650M</span>
                    <span className="stat-label">Cost Savings</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="region-card">
              <div className="region-header">
                <h3>Europe</h3>
                <div className="region-flag">🇪🇺</div>
              </div>
              <div className="region-stats">
                <div className="stat-item">
                  <span className="stat-icon">🏭</span>
                  <div className="stat-content">
                    <span className="stat-value">120+</span>
                    <span className="stat-label">Facilities</span>
                  </div>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">🌍</span>
                  <div className="stat-content">
                    <span className="stat-value">620M</span>
                    <span className="stat-label">Tons CO₂ Saved</span>
                  </div>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">💰</span>
                  <div className="stat-content">
                    <span className="stat-value">480M</span>
                    <span className="stat-label">Cost Savings</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="region-card">
              <div className="region-header">
                <h3>Asia-Pacific</h3>
                <div className="region-flag">🌏</div>
              </div>
              <div className="region-stats">
                <div className="stat-item">
                  <span className="stat-icon">🏭</span>
                  <div className="stat-content">
                    <span className="stat-value">230+</span>
                    <span className="stat-label">Facilities</span>
                  </div>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">🌍</span>
                  <div className="stat-content">
                    <span className="stat-value">830M</span>
                    <span className="stat-label">Tons CO₂ Saved</span>
                  </div>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">💰</span>
                  <div className="stat-content">
                    <span className="stat-value">670M</span>
                    <span className="stat-label">Cost Savings</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="sustainability-section">
        <div className="container">
          <div className="sustainability-content">
            <div className="sustainability-text">
              <h2>Our Sustainability Commitment</h2>
              <p>We're not just tracking impact - we're actively working to accelerate the transition to a circular economy</p>
              
              <div className="commitments">
                <div className="commitment">
                  <div className="commitment-icon">🎯</div>
                  <div className="commitment-content">
                    <h4>Science-Based Targets</h4>
                    <p>Aligned with 1.5°C climate goals and UN Sustainable Development Goals</p>
                  </div>
                </div>
                
                <div className="commitment">
                  <div className="commitment-icon">🤝</div>
                  <div className="commitment-content">
                    <h4>Partnership Approach</h4>
                    <p>Collaborating with governments, NGOs, and industry leaders</p>
                  </div>
                </div>
                
                <div className="commitment">
                  <div className="commitment-icon">🔬</div>
                  <div className="commitment-content">
                    <h4>Continuous Innovation</h4>
                    <p>Investing in research and development of new circular solutions</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="sustainability-visual">
              <div className="impact-tree">
                <div className="tree-trunk">
                  <div className="trunk-section">
                    <div className="section-label">Foundation</div>
                    <div className="section-value">Data Collection</div>
                  </div>
                  <div className="trunk-section">
                    <div className="section-label">Process</div>
                    <div className="section-value">AI Classification</div>
                  </div>
                  <div className="trunk-section">
                    <div className="section-label">Connection</div>
                    <div className="section-value">Smart Matching</div>
                  </div>
                </div>
                <div className="tree-branches">
                  <div className="branch">
                    <div className="branch-icon">🌍</div>
                    <div className="branch-label">Environmental Impact</div>
                  </div>
                  <div className="branch">
                    <div className="branch-icon">💰</div>
                    <div className="branch-label">Economic Benefits</div>
                  </div>
                  <div className="branch">
                    <div className="branch-icon">🤝</div>
                    <div className="branch-label">Social Value</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Join the Movement</h2>
            <p>Be part of the solution to global waste challenges</p>
            <div className="cta-buttons">
              <button className="btn btn-primary btn-large">Get Started</button>
              <button className="btn btn-secondary btn-large">View Case Studies</button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Impact;