import sys
import os
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from brain.src.api.app import app


client = TestClient(app)

def test_health():
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("\n[SUCCESS] FastAPI health endpoint test passed!")

if __name__ == "__main__":
    test_health()
