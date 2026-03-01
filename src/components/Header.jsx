import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState({});
  const [scrolled, setScrolled] = useState(false);
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
    setIsMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handleStorage = () => syncAuthState();
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  const handleLogout = () => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem('user');
        localStorage.removeItem('isLoggedIn');
      }
    } catch {
      // silently fail
    }
    window.location.href = '/login';
  };

  const isActive = (path) => location.pathname === path;

  const navLinks = [
    { to: '/', label: 'Home' },
    ...(isLoggedIn ? [{ to: '/dashboard', label: 'Dashboard' }] : []),
    { to: '/about', label: 'About' },
    { to: '/how-it-works', label: 'How It Works' },
    { to: '/marketplace', label: 'Marketplace' },
    { to: '/matches', label: 'Matches' },
    { to: '/classify', label: 'Classification' },
  ];

  return (
    <header className={`header ${scrolled ? 'header--scrolled' : ''}`}>
      <div className="container">
        <div className="header-content">
          <Link to="/" className="logo">
            <span className="logo-icon">♻️</span>
            <span className="logo-text">CircularEco</span>
          </Link>

          <nav className={`nav-menu ${isMenuOpen ? 'active' : ''}`}>
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`nav-link ${isActive(link.to) ? 'nav-link--active' : ''}`}
                onClick={() => setIsMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="header-actions">
            {isLoggedIn ? (
              <div className="user-menu">
                <Link to="/profile" className="user-pill">
                  <span className="user-pill-avatar">
                    {(user.company_name || user.email || '?')[0].toUpperCase()}
                  </span>
                  <span className="user-pill-name">
                    {user.company_name || user.email}
                  </span>
                </Link>
                <button className="btn btn-sm btn-outline" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            ) : (
              <>
                <Link to="/login" className="btn btn-sm btn-ghost">Sign In</Link>
                <Link to="/signup" className="btn btn-sm btn-primary">Get Started</Link>
              </>
            )}
            <button
              className={`menu-toggle ${isMenuOpen ? 'open' : ''}`}
              onClick={toggleMenu}
              aria-label="Toggle menu"
            >
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