import os
import sys

os.environ["TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hw_fastapi'))

import pytest
import httpx
from fastapi.testclient import TestClient

import main
from database import Base, engine

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers():
    client.post("/register", params={"username": "test", "password": "123"})
    r = client.post("/login", params={"username": "test", "password": "123"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register():
    r = client.post("/register", params={"username": "user", "password": "123"})
    assert r.status_code == 200


def test_register_duplicate():
    client.post("/register", params={"username": "dup", "password": "123"})
    r = client.post("/register", params={"username": "dup", "password": "123"})
    assert r.status_code == 400


def test_login():
    client.post("/register", params={"username": "u", "password": "p"})
    r = client.post("/login", params={"username": "u", "password": "p"})
    assert r.status_code == 200


def test_login_wrong():
    client.post("/register", params={"username": "u2", "password": "p"})
    r = client.post("/login", params={"username": "u2", "password": "wrong"})
    assert r.status_code == 401


def test_tasks_flow(auth_headers):
    r = client.post("/tasks", params={"title": "A", "priority": 1}, headers=auth_headers)
    task_id = r.json()["id"]
    r = client.get("/tasks", headers=auth_headers)
    assert len(r.json()) == 1
    r = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert r.json()["title"] == "A"
    client.put(f"/tasks/{task_id}", params={"status": "done"}, headers=auth_headers)
    r = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert r.json()["status"] == "done"
    r = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert r.status_code == 200


def test_task_404(auth_headers):
    assert client.get("/tasks/999", headers=auth_headers).status_code == 404
    assert client.put("/tasks/999", params={"status": "done"}, headers=auth_headers).status_code == 404
    assert client.delete("/tasks/999", headers=auth_headers).status_code == 404


def test_no_auth():
    r = client.post("/tasks", params={"title": "A"})
    assert r.status_code == 401


def test_top_tasks(auth_headers):
    client.post("/tasks", params={"title": "low", "priority": 1}, headers=auth_headers)
    client.post("/tasks", params={"title": "high", "priority": 10}, headers=auth_headers)
    r = client.get("/tasks/top", params={"n": 1}, headers=auth_headers)
    assert r.json()[0]["priority"] == 10


def test_search(auth_headers):
    client.post("/tasks", params={"title": "важная задача"}, headers=auth_headers)
    r = client.get("/tasks", params={"search": "важная"}, headers=auth_headers)
    assert len(r.json()) == 1


def test_httpx_request():
    import asyncio
    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post("/register", params={"username": "htt", "password": "123"})
            login = await ac.post("/login", params={"username": "htt", "password": "123"})
            token = login.json()["access_token"]
            h = {"Authorization": f"Bearer {token}"}
            r = await ac.post("/tasks", params={"title": "httpx"}, headers=h)
            assert r.status_code == 200

    asyncio.run(run())
