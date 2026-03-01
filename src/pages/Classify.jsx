import React, { useState, useEffect } from 'react';
import './Classify.css';

const Classify = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [classificationResult, setClassificationResult] = useState(null);
  const [matchedCompanies, setMatchedCompanies] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState('');
  // eslint-disable-next-line no-unused-vars
  const [backendStatus, setBackendStatus] = useState('checking');

  // Check backend status on component mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('/api/health');
        const data = await response.json();
        setBackendStatus(data.model_loaded ? 'connected' : 'model_missing');
      } catch {
        setBackendStatus('disconnected');
      }
    };
    
    checkBackend();
  }, []);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target.result);
        setClassificationResult(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleClassify = async () => {
    if (!selectedImage) return;
    
    setIsProcessing(true);
    setMessage('');
    setMatchedCompanies([]);
    
    try {
      // Convert base64 image to blob
      const response = await fetch(selectedImage);
      const blob = await response.blob();
      
      // Create FormData
      const formData = new FormData();
      formData.append('image', blob, 'waste-image.jpg');
      
      // Send to backend API
      const apiResponse = await fetch('/api/classify', {
        method: 'POST',
        body: formData,
      });
      
      if (!apiResponse.ok) {
        throw new Error(`API error: ${apiResponse.status}`);
      }
      
      const results = await apiResponse.json();
      setClassificationResult(results);

      // Fetch matching companies based on top waste type
      if (results.wasteTypes && results.wasteTypes.length > 0) {
        const topWasteType = results.wasteTypes[0].name;
        try {
          const userStr = localStorage.getItem('user');
          const currentUser = userStr ? JSON.parse(userStr) : null;
          const excludeParam = currentUser?.id ? `&exclude_user_id=${currentUser.id}` : '';
          const matchResponse = await fetch(`/api/match-companies?waste_type=${encodeURIComponent(topWasteType)}${excludeParam}`);
          if (matchResponse.ok) {
            const matchData = await matchResponse.json();
            setMatchedCompanies(matchData.matches || []);
          }
        } catch (matchErr) {
          console.error('Match fetch error:', matchErr);
        }
      }
      
    } catch (error) {
      console.error('Classification error:', error);
      setMessage('Unable to classify image. Please try again or check your connection.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="classify">
      <section className="classify-hero">
        <div className="container">
          <h1>AI Waste Classification</h1>
          <p className="subtitle">Upload an image and get instant waste identification powered by computer vision</p>
        </div>
      </section>

      <section className="classify-content">
        <div className="container">
          <div className="classify-interface">
            <div className="upload-section">
              <div className="upload-area">
                {!selectedImage ? (
                  <div className="upload-placeholder">
                    <div className="upload-icon">📸</div>
                    <h3>Upload Waste Image</h3>
                    <p>Take a photo or select an image of your industrial waste</p>
                    <label className="btn btn-primary">
                      Choose Image
                      <input 
                        type="file" 
                        accept="image/*" 
                        onChange={handleImageUpload}
                        style={{display: 'none'}}
                      />
                    </label>
                  </div>
                ) : (
                  <div className="image-preview">
                    <img src={selectedImage} alt="Waste preview" />
                    <button 
                      className="btn btn-secondary"
                      onClick={() => setSelectedImage(null)}
                    >
                      Change Image
                    </button>
                  </div>
                )}
              </div>
              
              {selectedImage && (
                <button 
                  className={`btn btn-primary btn-large classify-button ${isProcessing ? 'processing' : ''}`}
                  onClick={handleClassify}
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <>
                      <span className="processing-spinner"></span>
                      Analyzing...
                    </>
                  ) : (
                    'Classify Waste'
                  )}
                </button>
              )}

              {message && (
                <div className="error-message">{message}</div>
              )}
            </div>

            {classificationResult && (
              <div className="results-section">
                <h2>Classification Results</h2>
                
                <div className="waste-types">
                  <h3>Identified Waste Types</h3>
                  <div className="types-grid">
                    {classificationResult.wasteTypes.map((type, index) => (
                      <div key={index} className="type-card">
                        <div className="type-icon">{type.icon}</div>
                        <h4>{type.name}</h4>
                        <div className="confidence">
                          <div className="confidence-bar">
                            <div 
                              className="confidence-fill" 
                              style={{width: `${type.confidence}%`}}
                            ></div>
                          </div>
                          <span className="confidence-percent">{type.confidence}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="potential-uses">
                  <h3>Potential Applications</h3>
                  <ul>
                    {classificationResult.potentialUses.map((use, index) => (
                      <li key={index}>{use}</li>
                    ))}
                  </ul>
                </div>

                <div className="value-estimate">
                  <h3>Estimated Value</h3>
                  <div className="value-display">
                    {classificationResult.estimatedValue}
                  </div>
                </div>

                <div className="environmental-impact">
                  <h3>Environmental Impact</h3>
                  <div className="impact-grid">
                    <div className="impact-item">
                      <div className="impact-icon">🌍</div>
                      <div className="impact-text">
                        <span className="impact-value">{classificationResult.environmentalImpact.co2Saved}</span>
                        <span className="impact-label">CO₂ Saved</span>
                      </div>
                    </div>
                    <div className="impact-item">
                      <div className="impact-icon">🗑️</div>
                      <div className="impact-text">
                        <span className="impact-value">{classificationResult.environmentalImpact.landfillDiverted}</span>
                        <span className="impact-label">Landfill Diverted</span>
                      </div>
                    </div>
                    <div className="impact-item">
                      <div className="impact-icon">⚡</div>
                      <div className="impact-text">
                        <span className="impact-value">{classificationResult.environmentalImpact.energyRecovered}</span>
                        <span className="impact-label">Energy Recovered</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="next-steps">
                  <h3>Next Steps</h3>
                  <div className="steps-grid">
                    <div className="step">
                      <div className="step-number">1</div>
                      <div className="step-content">
                        <h4>Create Marketplace Listing</h4>
                        <p>List this waste on our platform to find buyers</p>
                      </div>
                    </div>
                    <div className="step">
                      <div className="step-number">2</div>
                      <div className="step-content">
                        <h4>Connect with Partners</h4>
                        <p>Get matched with companies who can use your waste</p>
                      </div>
                    </div>
                    <div className="step">
                      <div className="step-number">3</div>
                      <div className="step-content">
                        <h4>Track Impact</h4>
                        <p>Monitor environmental and financial benefits</p>
                      </div>
                    </div>
                  </div>
                  <button className="btn btn-primary btn-large">
                    Create Listing
                  </button>
                </div>

                {matchedCompanies.length > 0 && (
                  <div className="matched-companies">
                    <h3>🤝 Matched Companies</h3>
                    <p className="match-subtitle">
                      These companies can process or reuse your <strong>{classificationResult.wasteTypes[0].name}</strong> waste
                    </p>
                    <div className="companies-grid">
                      {matchedCompanies.map((company) => (
                        <div key={company.id} className="company-card">
                          <div className="company-avatar">
                            {company.company_name.charAt(0)}
                          </div>
                          <div className="company-info">
                            <h4>{company.company_name}</h4>
                            <span className="company-industry">{company.industry_type}</span>
                            {company.location && (
                              <span className="company-location">📍 {company.location}</span>
                            )}
                          </div>
                          <a href={`mailto:${company.email}`} className="btn btn-secondary btn-small">
                            Contact
                          </a>
                        </div>
                      ))}
                    </div>
                    {matchedCompanies.length > 5 && (
                      <p className="match-note">Showing all {matchedCompanies.length} matching companies</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="technology-section">
        <div className="container">
          <div className="tech-content">
            <div className="tech-text">
              <h2>Advanced AI Technology</h2>
              <p>Our classification system uses state-of-the-art computer vision and machine learning algorithms</p>
              <ul className="tech-features">
                <li>Convolutional Neural Networks for image recognition</li>
                <li>Transfer learning from pre-trained models</li>
                <li>Multi-label classification for complex waste streams</li>
                <li>Continuous learning from new data</li>
              </ul>
            </div>
            <div className="tech-visual">
              <div className="ai-diagram">
                <div className="ai-layer">
                  <div className="layer-icon">📷</div>
                  <span>Image Input</span>
                </div>
                <div className="ai-layer">
                  <div className="layer-icon">🧠</div>
                  <span>Neural Network</span>
                </div>
                <div className="ai-layer">
                  <div className="layer-icon">📊</div>
                  <span>Classification</span>
                </div>
                <div className="ai-layer">
                  <div className="layer-icon">📈</div>
                  <span>Results</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Classify;