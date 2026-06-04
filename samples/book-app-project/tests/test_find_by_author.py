import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


def test_find_by_author_partial_match_returns_books():
    collection = BookCollection()
    collection.add_book("Book A", "Joanne Smith", 2000)
    collection.add_book("Book B", "Annabelle Lee", 2001)
    collection.add_book("Book C", "John Doe", 1999)

    results = collection.find_by_author("ann")
    titles = {b.title for b in results}
    assert titles == {"Book A", "Book B"}


def test_find_by_author_case_variations_matches():
    collection = BookCollection()
    collection.add_book("Book A", "Anne Rice", 1985)
    collection.add_book("Book B", "Annie Proulx", 1990)

    results = collection.find_by_author("ANNE")
    titles = {b.title for b in results}
    assert titles == {"Book A", "Book B"}


def test_find_by_author_no_matches_returns_empty():
    collection = BookCollection()
    collection.add_book("Book A", "Alice", 2000)

    results = collection.find_by_author("Zelda")
    assert results == []
