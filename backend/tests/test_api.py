# backend/tests/test_api.py
from fastapi.testclient import TestClient

def get_client():
    from main import app
    return TestClient(app)

def test_health_check_returns_ok():
    client = get_client()
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "antennas" in data

def test_unknown_antenna_type_returns_404():
    client = get_client()
    r = client.post("/simulate/totally_unknown_antenna_xyz", json={
        "antenna_type": "totally_unknown_antenna_xyz",
        "antenna_params": {},
        "conductor": {}
    })
    assert r.status_code == 404

def test_simulate_endpoint_exists():
    client = get_client()
    # Just verify the route pattern works — 404 on unknown type, not 422 or 405
    r = client.post("/simulate/dipole", json={
        "antenna_type": "dipole",
        "antenna_params": {"frequency_mhz": 300, "length_mm": 475},
        "conductor": {"material": "copper", "cross_section": "round", "radius_mm": 1.0}
    })
    # Will be 200 (if openEMS available) or 500 (if not) — but NOT 404 or 422
    assert r.status_code in (200, 500)
