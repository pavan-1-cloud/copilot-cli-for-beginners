import sys
import os
import importlib
from pathlib import Path

import pytest

# Ensure the samples package path is first so we import project's books/utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import books
import utils


def reload_app_with_temp(tmp_path, monkeypatch):
    temp_file = tmp_path / "data.json"
    # ensure empty starting file
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))
    # reload modules to pick up patched DATA_FILE
    importlib.reload(books)
    if 'book_app' in sys.modules:
        del sys.modules['book_app']
    book_app = importlib.import_module('book_app')
    return book_app


def test_add_and_list(tmp_path, monkeypatch, capsys):
    book_app = reload_app_with_temp(tmp_path, monkeypatch)

    # simulate interactive inputs for get_book_details: title, author, year
    inputs = iter(["CLI Title", "CLI Author", "1999"])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))

    book_app.handle_add()
    _ = capsys.readouterr()

    book_app.handle_list()
    captured = capsys.readouterr()
    assert "CLI Title" in captured.out


def test_find_and_search(tmp_path, monkeypatch, capsys):
    book_app = reload_app_with_temp(tmp_path, monkeypatch)
    # add two books
    inputs1 = iter(["FindMe", "Find Author", "2005"])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs1))
    book_app.handle_add()

    inputs2 = iter(["Other", "Other Author", "2010"])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs2))
    book_app.handle_add()

    # simulate input for find by author
    monkeypatch.setattr('builtins.input', lambda prompt='': 'Find Author')
    book_app.handle_find()
    captured = capsys.readouterr()
    assert "FindMe" in captured.out

    # search with direct query
    book_app.handle_search('Other')
    captured = capsys.readouterr()
    assert "Other" in captured.out


def test_mark_and_remove(tmp_path, monkeypatch, capsys):
    book_app = reload_app_with_temp(tmp_path, monkeypatch)
    inputs = iter(["ToMark", "MAuthor", "2015"])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))
    book_app.handle_add()

    # mark
    book_app.handle_mark('ToMark')
    captured = capsys.readouterr()
    assert "marked as read" in captured.out

    # remove
    monkeypatch.setattr('builtins.input', lambda prompt='': 'ToMark')
    book_app.handle_remove()
    captured = capsys.readouterr()
    assert "removed" in captured.out
