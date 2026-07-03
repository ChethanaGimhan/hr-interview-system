from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
def test_parse_cv_rejects_bad_api_key():
    response = client.post(
        "/parse-cv",
        headers={"x-api-key": "wrong-key"},
        json={"cv_text": "this is a long enough cv text for validation", "job_role": "SWE"}
    )
    assert response.status_code == 401