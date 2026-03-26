import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Header.css';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState({});
  const [scrolled, setScrolled] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const notifRef = useRef(null);
  const location = useLocation();
  const navigate = useNavigate();

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

  // ── Notification polling ──
  const fetchUnreadCount = useCallback(() => {
    if (!user?.id) return;
    fetch(`/api/notifications/count?user_id=${user.id}`)
      .then(r => r.json())
      .then(d => setUnreadCount(d.unread || 0))
      .catch(() => {});
  }, [user?.id]);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 5000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  const loadNotifications = () => {
    if (!user?.id) return;
    fetch(`/api/notifications?user_id=${user.id}&limit=20`)
      .then(r => r.json())
      .then(d => {
        setNotifications(d.notifications || []);
        setUnreadCount(d.unread_count || 0);
      })
      .catch(() => {});
  };

  const toggleNotifications = () => {
    if (!notifOpen) loadNotifications();
    setNotifOpen(prev => !prev);
  };

  const handleNotifClick = (n) => {
    // Mark as read
    if (!n.is_read) {
      fetch(`/api/notifications/${n.id}/read`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id }),
      }).then(() => {
        setNotifications(prev => prev.map(x => x.id === n.id ? { ...x, is_read: true } : x));
        setUnreadCount(prev => Math.max(0, prev - 1));
      }).catch(() => {});
    }
    setNotifOpen(false);
    if (n.link) navigate(n.link);
  };

  const markAllRead = () => {
    if (!user?.id) return;
    fetch('/api/notifications/read-all', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id }),
    }).then(() => {
      setNotifications(prev => prev.map(x => ({ ...x, is_read: true })));
      setUnreadCount(0);
    }).catch(() => {});
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) setNotifOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const notifIcon = (type) => {
    if (type === 'message') return '💬';
    if (type === 'deal_created') return '🤝';
    if (type === 'deal_completed') return '✅';
    if (type === 'deal_cancelled') return '❌';
    return '🔔';
  };

  const timeAgo = (iso) => {
    const diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

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
    { to: '/network', label: 'Network' },
    { to: '/chat', label: 'Chat' },
    ...(isLoggedIn ? [{ to: '/deals', label: 'Deals' }] : []),
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
                {/* Notification Bell */}
                <div className="notif-wrapper" ref={notifRef}>
                  <button className="notif-bell" onClick={toggleNotifications} aria-label="Notifications">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                    </svg>
                    {unreadCount > 0 && (
                      <span className="notif-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
                    )}
                  </button>

                  {notifOpen && (
                    <div className="notif-dropdown">
                      <div className="notif-dropdown-header">
                        <h4>Notifications</h4>
                        {unreadCount > 0 && (
                          <button className="notif-mark-all" onClick={markAllRead}>Mark all read</button>
                        )}
                      </div>
                      <div className="notif-dropdown-list">
                        {notifications.length === 0 ? (
                          <div className="notif-empty">No notifications yet</div>
                        ) : (
                          notifications.map(n => (
                            <button
                              key={n.id}
                              className={`notif-item ${!n.is_read ? 'notif-unread' : ''}`}
                              onClick={() => handleNotifClick(n)}
                            >
                              <span className="notif-item-icon">{notifIcon(n.type)}</span>
                              <div className="notif-item-content">
                                <span className="notif-item-title">{n.title}</span>
                                {n.body && <span className="notif-item-body">{n.body}</span>}
                                <span className="notif-item-time">{timeAgo(n.created_at)}</span>
                              </div>
                              {!n.is_read && <span className="notif-item-dot"></span>}
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>

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