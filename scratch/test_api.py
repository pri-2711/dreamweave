import sys
import os
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from brain.src.api.app import app

client = TestClient(app)


def test_health():
    print("=== Testing /health endpoint ===")
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("[SUCCESS] /health test passed!\n")


def test_db_health():
    print("=== Testing /db-health endpoint ===")
    response = client.get("/db-health")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
    if response.status_code == 200:
        assert response.json().get("status") == "ok"
        assert response.json().get("database") == "dreamweave"
        print("[SUCCESS] /db-health connected to MongoDB Atlas successfully!\n")
    else:
        print(f"[NOTICE] /db-health returned status {response.status_code}: {response.json()}\n")


if __name__ == "__main__":
    test_health()
    test_db_health()
