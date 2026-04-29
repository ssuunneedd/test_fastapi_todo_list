import os
import sys

os.environ["TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hw_fastapi'))

from unittest.mock import MagicMock
from fastapi import HTTPException
from jose import jwt

from auth import create_token, SECRET_KEY, ALGORITHM
from models import User, Task
import database


def test_create_token():
    token = create_token({"user_id": 5})
    data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert data["user_id"] == 5


def test_user_model():
    user = User(username="olya", password="123")
    assert user.username == "olya"


def test_task_model():
    task = Task(title="дело", priority=3, user_id=1)
    assert task.title == "дело"
    assert task.priority == 3


def test_get_current_user():
    token = create_token({"user_id": 1})
    fake_token = MagicMock()
    fake_token.credentials = token
    fake_user = MagicMock()
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = fake_user
    assert database.get_current_user(token=fake_token, db=fake_db) == fake_user


def test_get_current_user_bad_token():
    fake_token = MagicMock()
    fake_token.credentials = "bad.token"
    try:
        database.get_current_user(token=fake_token, db=MagicMock())
        assert False
    except HTTPException as e:
        assert e.status_code == 401
