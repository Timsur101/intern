import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base, get_db
from main import app
from models import VirtualMachine, User

engine_test = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine_test)

Base.metadata.create_all(bind=engine_test)


def override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean():
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)


def register_user(email="test@test.com", password="pass123"):
    with patch("main.send_activation_email.delay"):
        r = client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "password_confirm": password,
        })
    return r


def test_register():
    r = register_user()
    assert r.status_code == 200


def test_register_duplicate():
    register_user()
    r = register_user()
    assert r.status_code == 400


def test_register_passwords_mismatch():
    with patch("main.send_activation_email.delay"):
        r = client.post("/api/auth/register", json={
            "email": "a@a.com",
            "password": "111",
            "password_confirm": "222",
        })
    assert r.status_code == 400


def test_login():
    register_user()
    r = client.post("/api/auth/login", json={"email": "test@test.com", "password": "pass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_pass():
    register_user()
    r = client.post("/api/auth/login", json={"email": "test@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_activate_key_no_vms():
    register_user()
    db = TestSession()
    user = db.query(User).first()
    key = user.activation_key
    db.close()

    r = client.post("/api/activate-key", json={"key": key})
    assert r.status_code == 503


def test_activate_key_ok():
    register_user()
    db = TestSession()
    user = db.query(User).first()
    key = user.activation_key
    db.add(VirtualMachine(name="p1", host="1.2.3.4", port=1080, protocol="socks5"))
    db.commit()
    db.close()

    r = client.post("/api/activate-key", json={"key": key})
    assert r.status_code == 200
    assert r.json()["host"] == "1.2.3.4"


def test_activate_key_invalid():
    r = client.post("/api/activate-key", json={"key": "wrongkey123"})
    assert r.status_code == 400
