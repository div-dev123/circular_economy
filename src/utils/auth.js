// Lightweight auth helper: stores access token and refreshes when needed
export function setAccessToken(token) {
  try {
    localStorage.setItem('access_token', token);
  } catch (e) {}
}

export function getAccessToken() {
  try {
    return localStorage.getItem('access_token');
  } catch (e) {
    return null;
  }
}

export function clearAuth() {
  try {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.setItem('isLoggedIn', 'false');
    window.dispatchEvent(new Event('storage'));
  } catch (e) {}
}

export async function refreshAccessToken() {
  // Calls backend /api/auth/refresh which relies on httpOnly refresh cookie
  try {
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (data && data.access_token) {
      setAccessToken(data.access_token);
      return data.access_token;
    }
    return null;
  } catch (e) {
    return null;
  }
}

export async function fetchWithAuth(input, init = {}) {
  const opts = Object.assign({}, init);
  opts.credentials = opts.credentials || 'include';
  opts.headers = Object.assign({}, opts.headers);

  const token = getAccessToken();
  if (token) opts.headers['Authorization'] = `Bearer ${token}`;

  let res = await fetch(input, opts);
  if (res.status === 401) {
    // Try refresh once
    const newToken = await refreshAccessToken();
    if (newToken) {
      opts.headers['Authorization'] = `Bearer ${newToken}`;
      res = await fetch(input, opts);
    } else {
      // Clear auth if refresh failed
      clearAuth();
    }
  }
  return res;
}
