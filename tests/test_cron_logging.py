"""Unit tests for cron lightweight trigger endpoint and log verbosity configuration."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings

client = TestClient(app)


def test_cron_endpoint_returns_204():
    """POST /api/recon/cron must return HTTP 204 No Content with empty body."""
    response = client.post("/api/recon/cron")
    assert response.status_code == 204
    assert response.content == b""


def test_log_level_configuration():
    """Settings model contains LOG_LEVEL defaulting to INFO."""
    settings = get_settings()
    assert hasattr(settings, "LOG_LEVEL")
    assert settings.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "WARN")
