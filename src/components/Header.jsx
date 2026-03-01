import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState({});
  const location = useLocation();

  const syncAuthState = () => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const loggedIn = localStorage.getItem('isLoggedIn') === 'true';
        setIsLoggedIn(loggedIn);
        if (loggedIn) {
          const userData = JSON.parse(localStorage.getItem('user') || '{}');
          setUser(userData);
        } else {
          setUser({});
        }
      }
    } catch {
      setIsLoggedIn(false);
      setUser({});
    }
  };

  useEffect(() => {
    syncAuthState();
  }, [location.pathname]);

  useEffect(() => {
    const handleStorage = () => syncAuthState();
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const handleLogout = () => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem('user');
        localStorage.removeItem('isLoggedIn');
      }
    } catch (e) {
      // localStorage not available, silently fail
    }
    window.location.href = '/login';
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
            {isLoggedIn ? (
              <div className="user-menu">
                <Link to="/profile" className="btn btn-secondary">
                  {user.company_name || user.email}
                </Link>
                <button className="btn btn-outline" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            ) : (
              <>
                <Link to="/login" className="btn btn-secondary">Sign In</Link>
                <Link to="/signup" className="btn btn-primary">Get Started</Link>
              </>
            )}
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