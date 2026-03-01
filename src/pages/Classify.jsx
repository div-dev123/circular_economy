import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Classify.css';

const MATCHING_STEPS = [
  { label: 'Applying rule-based compatibility filter…', icon: '📋' },
  { label: 'Computing ML cosine similarity vectors…', icon: '🧠' },
  { label: 'Running KNN cluster analysis…', icon: '🔬' },
  { label: 'Calculating geographic proximity scores…', icon: '📍' },
  { label: 'Optimising with linear programming…', icon: '⚙️' },
  { label: 'Ranking and finalising matches…', icon: '🏆' },
];

const Classify = () => {
  const navigate = useNavigate();
  const [selectedImage, setSelectedImage] = useState(null);
  const [classificationResult, setClassificationResult] = useState(null);
  const [matchedCompanies, setMatchedCompanies] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState('');
  // eslint-disable-next-line no-unused-vars
  const [backendStatus, setBackendStatus] = useState('checking');
  const [isFindingMatches, setIsFindingMatches] = useState(false);
  const [matchProgress, setMatchProgress] = useState(0);
  const [matchStepIdx, setMatchStepIdx] = useState(0);
  const matchTimerRef = useRef(null);

  const handleFindMatches = () => {
    if (!classificationResult?.wasteTypes?.length) return;
    setIsFindingMatches(true);
    setMatchProgress(0);
    setMatchStepIdx(0);

    const totalDuration = 5000;
    const stepInterval = totalDuration / MATCHING_STEPS.length;
    const tickInterval = 50;
    let elapsed = 0;

    matchTimerRef.current = setInterval(() => {
      elapsed += tickInterval;
      const pct = Math.min((elapsed / totalDuration) * 100, 100);
      setMatchProgress(pct);
      setMatchStepIdx(Math.min(Math.floor(elapsed / stepInterval), MATCHING_STEPS.length - 1));

      if (elapsed >= totalDuration) {
        clearInterval(matchTimerRef.current);
        const topType = classificationResult.wasteTypes[0].name.toLowerCase();
        navigate(`/matches?waste_type=${encodeURIComponent(topType)}`);
      }
    }, tickInterval);
  };

  useEffect(() => {
    return () => { if (matchTimerRef.current) clearInterval(matchTimerRef.current); };
  }, []);

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

                {/* Find Matches CTA */}
                <div className="find-matches-cta">
                  <button
                    className="btn btn-primary btn-large find-matches-btn"
                    onClick={handleFindMatches}
                    disabled={isFindingMatches}
                  >
                    🤖 Find Matching Companies
                  </button>
                  {matchedCompanies.length > 0 && (
                    <p className="quick-match-note">
                      {matchedCompanies.length} potential match{matchedCompanies.length !== 1 ? 'es' : ''} found — click above for detailed AI scoring
                    </p>
                  )}
                </div>

                {/* Matching overlay */}
                {isFindingMatches && (
                  <div className="matching-overlay">
                    <div className="matching-modal">
                      <div className="matching-header">
                        <span className="matching-icon">🤖</span>
                        <h3>AI Matching Engine</h3>
                        <p>Analysing <strong>{classificationResult.wasteTypes[0].name}</strong> against registered companies</p>
                      </div>

                      <div className="matching-progress-bar">
                        <div className="matching-progress-fill" style={{ width: `${matchProgress}%` }} />
                      </div>
                      <span className="matching-pct">{Math.round(matchProgress)}%</span>

                      <div className="matching-steps">
                        {MATCHING_STEPS.map((step, i) => (
                          <div
                            key={i}
                            className={`matching-step ${
                              i < matchStepIdx ? 'done' : i === matchStepIdx ? 'active' : ''
                            }`}
                          >
                            <span className="step-icon">{i < matchStepIdx ? '✅' : i === matchStepIdx ? step.icon : '⏳'}</span>
                            <span className="step-label">{step.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
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