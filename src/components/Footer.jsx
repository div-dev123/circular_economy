import React from 'react';
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
              <li><a href="/marketplace">Marketplace</a></li>
              <li><a href="/classify">Waste Classification</a></li>
              <li><a href="/business">Business Solutions</a></li>
              <li><a href="/impact">Impact Dashboard</a></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3>Resources</h3>
            <ul>
              <li><a href="/about">About Circular Economy</a></li>
              <li><a href="/how-it-works">How It Works</a></li>
              <li><a href="/blog">Blog</a></li>
              <li><a href="/case-studies">Case Studies</a></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3>Support</h3>
            <ul>
              <li><a href="/contact">Contact Us</a></li>
              <li><a href="/help">Help Center</a></li>
              <li><a href="/privacy">Privacy Policy</a></li>
              <li><a href="/terms">Terms of Service</a></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2026 CircularEco. All rights reserved.</p>
          <div className="footer-links">
            <a href="/privacy">Privacy</a>
            <a href="/terms">Terms</a>
            <a href="/cookies">Cookies</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;