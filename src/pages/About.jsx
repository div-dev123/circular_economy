import React from 'react';
import './About.css';

const About = () => {
  return (
    <div className="about">
      <section className="about-hero">
        <div className="container">
          <h1>Understanding the Circular Economy</h1>
          <p className="subtitle">A regenerative system that eliminates waste and continually uses resources</p>
        </div>
      </section>

      <section className="principles-section">
        <div className="container">
          <div className="section-header">
            <h2>The Three Core Principles</h2>
            <p>Built on the foundation of Reduce, Reuse, and Recycle</p>
          </div>
          
          <div className="principles-grid">
            <div className="principle-card">
              <div className="principle-icon">🔻</div>
              <h3>Reduce</h3>
              <p>Design out waste and pollution from the start. Use fewer raw materials, choose sustainable inputs, make products more durable and efficient, and avoid single-use items.</p>
              <ul>
                <li>Prevent waste creation upstream</li>
                <li>Optimize resource efficiency</li>
                <li>Choose sustainable materials</li>
                <li>Design for longevity</li>
              </ul>
            </div>
            
            <div className="principle-card">
              <div className="principle-icon">🔄</div>
              <h3>Reuse</h3>
              <p>Keep products and components in use longer through repair, refurbishment, remanufacturing, sharing, or repurposing items.</p>
              <ul>
                <li>Repair and refurbish</li>
                <li>Leasing instead of buying</li>
                <li>Second-hand markets</li>
                <li>Product-as-a-service models</li>
              </ul>
            </div>
            
            <div className="principle-card">
              <div className="principle-icon">♻️</div>
              <h3>Recycle</h3>
              <p>Recover materials at the end of life by breaking down products into raw materials to feed back into new production, closing the loop.</p>
              <ul>
                <li>Material recovery</li>
                <li>Composting organics</li>
                <li>Industrial recycling</li>
                <li>Closed-loop systems</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="cycles-section">
        <div className="container">
          <div className="section-header">
            <h2>Closed Loop Systems</h2>
            <p>Two distinct cycles keep materials flowing in the circular economy</p>
          </div>
          
          <div className="cycles-grid">
            <div className="cycle-card biological">
              <h3>Biological Cycles</h3>
              <div className="cycle-icon">🌱</div>
              <p>Organic materials return to nature through natural processes</p>
              <div className="cycle-content">
                <div className="cycle-item">
                  <h4>Composting</h4>
                  <p>Food waste, textiles, and organic materials decompose naturally</p>
                </div>
                <div className="cycle-item">
                  <h4>Anaerobic Digestion</h4>
                  <p>Produces biogas and fertilizer from organic waste</p>
                </div>
                <div className="cycle-item">
                  <h4>Natural Regeneration</h4>
                  <p>Materials safely return to ecosystems</p>
                </div>
              </div>
            </div>
            
            <div className="cycle-card technical">
              <h3>Technical Cycles</h3>
              <div className="cycle-icon">⚙️</div>
              <p>Durable goods are recycled or remanufactured repeatedly</p>
              <div className="cycle-content">
                <div className="cycle-item">
                  <h4>Recycling</h4>
                  <p>Metals, plastics, and materials processed for reuse</p>
                </div>
                <div className="cycle-item">
                  <h4>Remanufacturing</h4>
                  <p>Products restored to like-new condition</p>
                </div>
                <div className="cycle-item">
                  <h4>Repurposing</h4>
                  <p>Materials given new life in different applications</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="symbiosis-section">
        <div className="container">
          <div className="symbiosis-content">
            <div className="symbiosis-text">
              <h2>Industrial Symbiosis</h2>
              <p>Companies collaborate so one's waste/by-product becomes another's input, creating mutual value while reducing environmental impact.</p>
              
              <div className="symbiosis-benefits">
                <div className="benefit">
                  <span className="benefit-icon">💰</span>
                  <div>
                    <h4>Cost Reduction</h4>
                    <p>Lower raw material and disposal costs</p>
                  </div>
                </div>
                <div className="benefit">
                  <span className="benefit-icon">🏭</span>
                  <div>
                    <h4>Resource Efficiency</h4>
                    <p>Maximize value from existing materials</p>
                  </div>
                </div>
                <div className="benefit">
                  <span className="benefit-icon">🌍</span>
                  <div>
                    <h4>Environmental Impact</h4>
                    <p>Reduce extraction and pollution</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="symbiosis-example">
              <h3>Real-World Example</h3>
              <div className="example-content">
                <div className="example-step">
                  <div className="step-number">1</div>
                  <div className="step-content">
                    <h4>Textile Factory</h4>
                    <p>Produces cotton waste</p>
                  </div>
                </div>
                <div className="example-step">
                  <div className="step-number">2</div>
                  <div className="step-content">
                    <h4>Insulation Manufacturer</h4>
                    <p>Uses cotton waste as raw material</p>
                  </div>
                </div>
                <div className="example-step">
                  <div className="step-number">3</div>
                  <div className="step-content">
                    <h4>Construction Company</h4>
                    <p>Uses recycled insulation</p>
                  </div>
                </div>
                <div className="result">
                  <span className="result-icon">✅</span>
                  <p>Waste eliminated, value created, environment protected</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;