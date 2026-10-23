import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.admin import validate_safe_url

client = TestClient(app)

def test_admin_access_denied_for_unauthenticated():
    """Unauthenticated users should be rejected entirely."""
    response = client.get("/api/v1/admin/kpis")
    assert response.status_code == 401

def test_safe_url_validation_blocks_ssrf():
    """Tests the SSRF validation prevents internal network scans."""
    # Should Pass
    validate_safe_url("https://example.com/api/jobs")
    validate_safe_url("http://public-jobs-board.org")
    
    # Should Fail
    with pytest.raises(ValueError):
        validate_safe_url("http://localhost:8000")
    
    with pytest.raises(ValueError):
        validate_safe_url("http://127.0.0.1/admin")
        
    with pytest.raises(ValueError):
        validate_safe_url("http://169.254.169.254/latest/meta-data/")
        
    with pytest.raises(ValueError):
        validate_safe_url("ftp://example.com")