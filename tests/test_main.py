from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

# Mock Redis before importing app
with patch('fastapi_cache.FastAPICache.init'), \
     patch('redis.asyncio.from_url'):
    from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "v1"

def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200

def test_register_missing_fields():
    response = client.post("/api/v1/auth/register", json={
        "email": "test@test.com"
        # missing full_name and password
    })
    assert response.status_code == 422  # Unprocessable Entity

def test_login_invalid_credentials():
    response = client.post("/api/v1/auth/login", data={
        "username": "nonexistent@email.com",
        "password": "wrongpassword"
    })
    assert response.status_code in [401, 422, 500]

def test_products_requires_auth():
    response = client.get("/api/v1/products/")
    assert response.status_code == 401

def test_customers_requires_auth():
    response = client.get("/api/v1/customers/")
    assert response.status_code == 401

def test_orders_requires_auth():
    response = client.get("/api/v1/orders/")
    assert response.status_code == 401

def test_analytics_requires_auth():
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 401