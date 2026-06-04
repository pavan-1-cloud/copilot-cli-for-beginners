import sqlite3
import hashlib
import pickle
import base64
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def db_conn(monkeypatch, tmp_path):
    # Create an in-memory sqlite DB for tests
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    # seed a user
    cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                ("Alice", "alice@example.com", "secret"))
    conn.commit()

    # Monkeypatch sqlite3.connect to return this connection for isolation
    monkeypatch.setattr(sqlite3, 'connect', lambda *args, **kwargs: conn)

    yield conn

    conn.close()


@pytest.fixture
def us_module():
    # Load the user_service module directly from file to avoid import path issues
    path = Path(__file__).parent / "user_service.py"
    spec = importlib.util.spec_from_file_location("user_service", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_get_and_cache_user(db_conn, us_module):
    us = us_module
    # ensure cache is empty
    us.user_cache.clear()

    user = us.get_user(1)
    assert user is not None
    assert user['email'] == 'alice@example.com'

    cached = us.get_cached_user(1)
    assert cached == user
    # cache should contain entry
    assert 1 in us.user_cache


def test_update_user_and_fetch(db_conn, us_module):
    us = us_module
    # update name
    us.update_user(1, {'name': 'AliceX'})
    user = us.get_user(1)
    assert user['name'] == 'AliceX'


def test_login_success_and_failure(db_conn, us_module, capsys):
    us = us_module
    # successful login
    res = us.login('alice@example.com', 'secret')
    assert res['success'] is True
    assert 'user' in res

    # wrong password
    res2 = us.login('alice@example.com', 'bad')
    assert res2['success'] is False


def test_verify_and_hash_password(us_module):
    us = us_module
    assert us.verify_password('a', 'a') is True
    assert us.verify_password('a', 'b') is False

    assert us.hash_password('pw') == hashlib.md5(b'pw').hexdigest()


def test_create_user_inserts(db_conn, us_module):
    us = us_module
    us.create_user({'name': 'Bob', 'email': 'bob@example.com', 'password': 'pwd'})
    cur = db_conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", ("bob@example.com",))
    row = cur.fetchone()
    assert row is not None
    assert row['name'] == 'Bob'


def test_generate_token_uses_jwt(monkeypatch, us_module):
    us = us_module
    called = {}

    class DummyJWT:
        @staticmethod
        def encode(payload, secret, algorithm=None):
            called['payload'] = payload
            called['secret'] = secret
            called['alg'] = algorithm
            return 'tok-123'

    monkeypatch.setitem(__import__('sys').modules, 'jwt', DummyJWT)
    token = us.generate_token(42)
    assert token == 'tok-123'
    assert called['payload']['user_id'] == 42
    assert isinstance(called['secret'], str)


def test_load_user_preferences_roundtrip(us_module):
    us = us_module
    obj = {'theme': 'dark', 'flags': [1, 2, 3]}
    data = base64.b64encode(pickle.dumps(obj))
    got = us.load_user_preferences(data)
    assert got == obj
