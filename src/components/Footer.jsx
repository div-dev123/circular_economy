import React from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <div className="footer-section">
            <div className="footer-logo">
              <span className="logo-icon">♻️</span>
              <span className="logo-text">CircularEco</span>
            </div>
            <p className="footer-description">
              Building a sustainable future through circular economy principles. 
              Connecting waste producers with innovative solutions.
            </p>
            <div className="social-links">
              <a href="#" className="social-link">📘</a>
              <a href="#" className="social-link">🐦</a>
              <a href="#" className="social-link">💼</a>
              <a href="#" className="social-link">📸</a>
            </div>
          </div>

          <div className="footer-section">
            <h3>Platform</h3>
            <ul>
              <li><Link to="/marketplace">Marketplace</Link></li>
              <li><Link to="/classify">Waste Classification</Link></li>
              <li><Link to="/business">Business Solutions</Link></li>
              <li><Link to="/impact">Impact Dashboard</Link></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3>Resources</h3>
            <ul>
              <li><Link to="/about">About Circular Economy</Link></li>
              <li><Link to="/how-it-works">How It Works</Link></li>
              <li><a href="#">Blog</a></li>
              <li><a href="#">Case Studies</a></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3>Support</h3>
            <ul>
              <li><Link to="/contact">Contact Us</Link></li>
              <li><a href="#">Help Center</a></li>
              <li><a href="#">Privacy Policy</a></li>
              <li><a href="#">Terms of Service</a></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2026 CircularEco. All rights reserved.</p>
          <div className="footer-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Cookies</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;