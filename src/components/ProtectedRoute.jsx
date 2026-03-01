import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();

  // Check auth synchronously on every render — no useEffect needed
  let isLoggedIn = false;
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    }
  } catch {
    isLoggedIn = false;
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
