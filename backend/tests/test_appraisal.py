"""
Appraisal API Tests
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_appraise_no_file():
    """Test appraisal endpoint without file."""
    response = client.post("/api/appraise")
    assert response.status_code == 422  # Validation error


def test_appraise_invalid_file_type():
    """Test appraisal endpoint with invalid file type."""
    response = client.post(
        "/api/appraise",
        files={"image": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
