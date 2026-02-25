import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <Link to="/" className="logo">
            <span className="logo-icon">♻️</span>
            <span className="logo-text">CircularEco</span>
          </Link>
          
          <nav className={`nav-menu ${isMenuOpen ? 'active' : ''}`}>
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/about" className="nav-link">About</Link>
            <Link to="/how-it-works" className="nav-link">How It Works</Link>
            <Link to="/marketplace" className="nav-link">Marketplace</Link>
            <Link to="/classify" className="nav-link">Waste Classification</Link>
            <Link to="/business" className="nav-link">Business Solutions</Link>
            <Link to="/impact" className="nav-link">Impact</Link>
            <Link to="/contact" className="nav-link">Contact</Link>
          </nav>

          <div className="header-actions">
            <button className="btn btn-primary">Get Started</button>
            <button className="menu-toggle" onClick={toggleMenu}>
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;