import pytest
from contextlib import contextmanager
from datetime import datetime

import books
from books import BookCollection, _parse_bool


def test_parse_bool_variants():
    assert _parse_bool(True) is True
    assert _parse_bool(False) is False
    assert _parse_bool(1) is True
    assert _parse_bool(0) is False
    assert _parse_bool("Yes") is True
    assert _parse_bool("no") is False
    assert _parse_bool("  Y ") is True
    assert _parse_bool(None) is False


def test_load_corrupted_json(tmp_path, monkeypatch):
    p = tmp_path / "data.json"
    p.write_text("{not valid json")
    monkeypatch.setattr(books, "DATA_FILE", str(p))
    coll = BookCollection()
    assert coll.list_books() == []


def test_save_books_handles_timeout(monkeypatch):
    coll = BookCollection()
    coll.add_book("Temp Timeout", "Author", 2000)

    @contextmanager
    def raising_lock(path, timeout=5.0, poll=0.05):
        raise TimeoutError("simulated timeout")
        yield

    monkeypatch.setattr(books, "_file_lock", raising_lock)

    # save_books should handle TimeoutError internally and not raise
    coll.save_books()


def test_load_uses_fallback_when_lock_unavailable(tmp_path, monkeypatch):
    p = tmp_path / "data.json"
    # valid JSON with one book
    p.write_text('[{"title": "X", "author": "Y", "year": 2001, "read": false}]')
    monkeypatch.setattr(books, "DATA_FILE", str(p))

    @contextmanager
    def raising_lock(path, timeout=5.0, poll=0.05):
        raise TimeoutError("simulated")
        yield

    monkeypatch.setattr(books, "_file_lock", raising_lock)

    coll = BookCollection()
    titles = [b.title for b in coll.list_books()]
    assert "X" in titles


def test_add_book_invalid_years():
    coll = BookCollection()
    future_year = datetime.utcnow().year + 1
    with pytest.raises(ValueError):
        coll.add_book("Bad Year", "Author", -1)
    with pytest.raises(ValueError):
        coll.add_book("Future Book", "Author", future_year)
