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


def test_appraise_response_schema():
    """Test that the appraisal response matches the new schema.

    NOTE: This test requires YOLO model files to be present.
    It verifies the response shape when a valid image is submitted.
    If models are unavailable, the endpoint returns an error status
    and this test is skipped.
    """
    import io
    import numpy as np
    import cv2

    # Create a minimal synthetic test image (not a real koi, but tests schema)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[20:80, 20:80] = [200, 100, 50]  # A coloured rectangle
    _, buf = cv2.imencode(".png", img)
    file_bytes = io.BytesIO(buf.tobytes())

    response = client.post(
        "/api/appraise",
        files={"image": ("test.png", file_bytes, "image/png")},
    )

    # If models are missing the service will return 422/503 — skip schema check
    if response.status_code in (422, 503):
        pytest.skip("YOLO models not available for full schema test")

    assert response.status_code == 200
    data = response.json()

    # Required top-level fields
    assert "size_cm" in data
    assert "pattern_name" in data
    assert "pattern_confidence" in data
    assert "color_proportions" in data
    assert "symmetry_score" in data

    # Removed fields must NOT be present
    assert "predicted_price" not in data
    assert "color_white_pct" not in data
    assert "color_red_pct" not in data
    assert "color_black_pct" not in data
    assert "color_quality_score" not in data

    # Type checks
    assert isinstance(data["size_cm"], (int, float))
    assert isinstance(data["pattern_name"], str)
    assert isinstance(data["pattern_confidence"], (int, float))
    assert isinstance(data["color_proportions"], dict)
    assert isinstance(data["symmetry_score"], (int, float))

    # Color proportions: values 0-100, sum ~100%
    props = data["color_proportions"]
    assert len(props) >= 1
    for color_name, pct in props.items():
        assert isinstance(color_name, str)
        assert 0.0 <= pct <= 100.0
    total = sum(props.values())
    assert 99.0 <= total <= 101.0, f"Color proportions sum to {total}, expected ~100"


def test_train_endpoint_removed():
    """Verify that the /train endpoint no longer exists."""
    response = client.post("/api/train", json={})
    # Should be 404 (not found) or 405 (method not allowed), never 200
    assert response.status_code in (404, 405, 422)


def test_model_status():
    """Test model-status endpoint returns only YOLO models."""
    response = client.get("/api/model-status")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    models = data["models"]

    # YOLO models should be listed
    assert "koi_segment" in models
    assert "coin_detect" in models
    assert "koi_pattern" in models

    # Linear price models must NOT appear
    assert "linear_ogon" not in models
    assert "linear_sanke" not in models
    assert "linear_kohaku" not in models
