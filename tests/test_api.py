import pytest
from main import app

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def test_health(client):
    """Verifica que el endpoint /api/health funcione"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

def test_index(client):
    """Verifica que el index.html se cargue correctamente"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"<!DOCTYPE html" in response.data or b"<html" in response.data
