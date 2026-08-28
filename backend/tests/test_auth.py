import json
import types
from datetime import datetime, timedelta

import pytest

from app import app, JWT_SECRET, JWT_ALGORITHM, REFRESH_TOKEN_EXPIRES_DAYS


class FakeRedisClient:
    def __init__(self):
        self.store = {}

    def setex(self, key, ttl, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        return self.store.pop(key, None)


class FakeRedisMgr:
    def __init__(self):
        self.client = FakeRedisClient()


class DummyDBManager:
    def __init__(self):
        self._redis = FakeRedisMgr()

    def authenticate_user(self, email, password):
        # Accept any email/password for tests
        return {'id': 123, 'email': email, 'company_name': 'TestCo'}

    def get_manager(self, name):
        if name == 'redis':
            return self._redis
        return None


@pytest.fixture(autouse=True)
def client(monkeypatch):
    # Monkeypatch db_manager in app module with dummy
    dummy = DummyDBManager()
    monkeypatch.setattr('app.db_manager', dummy)
    monkeypatch.setattr('app.DATABASE_AVAILABLE', True)
    with app.test_client() as c:
        yield c


def test_login_refresh_logout_flow(client):
    # Login
    resp = client.post('/api/auth/login', json={'email': 'a@b.com', 'password': 'pass'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'access_token' in data and 'refresh_token' in data

    # Refresh should succeed using cookie set by login (test_client stores cookies)
    refresh_resp = client.post('/api/auth/refresh')
    assert refresh_resp.status_code == 200
    refresh_data = refresh_resp.get_json()
    assert 'access_token' in refresh_data

    # Logout should clear refresh token and revoke jti
    logout_resp = client.post('/api/auth/logout')
    assert logout_resp.status_code == 200

    # After logout, refresh should fail
    refresh_resp2 = client.post('/api/auth/refresh')
    assert refresh_resp2.status_code == 401
