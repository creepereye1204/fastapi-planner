from fastapi.testclient import TestClient
from main import app  # main.py에서 FastAPI 앱을 가져옴
import pytest


client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI with Beanie and MongoDB"}


def test_create_item():
    item_data = {"description": "Test Item", "price": 10.0, "tax": 1.0}
    response = client.post("/items/", json=item_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["description"] == "Test Item"
    assert response.json()["price"] == 10.0
    assert response.json()["tax"] == 1.0


def test_get_items():
    response = client.get("/items/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
