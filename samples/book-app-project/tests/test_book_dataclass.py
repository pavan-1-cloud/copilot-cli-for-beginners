import os
import sys
import importlib.util

FILE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.dirname(FILE_DIR)
spec = importlib.util.spec_from_file_location("books", os.path.join(PROJECT_DIR, "books.py"))
books = importlib.util.module_from_spec(spec)
spec.loader.exec_module(books)
Book = books.Book


def test_default_read_is_false():
    b = Book(title="1984", author="Orwell", year=1949)
    assert b.read is False


def test_asdict_contains_expected_keys():
    from dataclasses import asdict
    d = asdict(Book(title="Dune", author="Herbert", year=1965))
    assert d == {"title": "Dune", "author": "Herbert", "year": 1965, "read": False}


def test_equality_for_same_values():
    b1 = Book("A", "B", 2000)
    b2 = Book("A", "B", 2000)
    assert b1 == b2
    b2.read = True
    assert b1 != b2


def test_mutability_of_read_field():
    b = Book("X", "Y", 1999)
    assert not b.read
    b.read = True
    assert b.read

