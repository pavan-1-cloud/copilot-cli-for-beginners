import pytest
from books import BookCollection, Book, _parse_bool


def test_add_and_persist(tmp_path):
    data_file = tmp_path / "data.json"
    col = BookCollection(str(data_file))
    b = col.add_book("The Hobbit", "J. R. R. Tolkien", 1937)
    assert isinstance(b, Book)
    assert b.title == "The Hobbit"

    # persisted to disk
    col2 = BookCollection(str(data_file))
    assert len(col2.list_books()) == 1
    found = col2.find_book_by_title("The Hobbit")
    assert found is not None
    assert found.author == "J. R. R. Tolkien"


def test_duplicate_title_raises(tmp_path):
    df = tmp_path / "d.json"
    col = BookCollection(str(df))
    col.add_book("Same Title", "Author A", 2000)
    with pytest.raises(ValueError):
        col.add_book("same title", "Author B", 2001)


def test_invalid_inputs(tmp_path):
    df = tmp_path / "d.json"
    col = BookCollection(str(df))
    with pytest.raises(ValueError):
        col.add_book("", "A", 2000)
    with pytest.raises(ValueError):
        col.add_book("T", "", 2000)
    with pytest.raises(ValueError):
        col.add_book("T", "A", "not-a-year")
    # future year
    future_year = 3000
    with pytest.raises(ValueError):
        col.add_book("Future", "Author", future_year)


def test_find_and_search(tmp_path):
    df = tmp_path / "d.json"
    col = BookCollection(str(df))
    col.add_book("Alpha", "Alice Example", 2001)
    col.add_book("Beta", "Bob Example", 2002)

    res = col.find_by_author("alice")
    assert len(res) == 1
    assert res[0].author == "Alice Example"

    assert col.search("beta")[0].title == "Beta"
    assert col.find_book_by_title(None) is None
    assert col.find_book_by_title("does not exist") is None


def test_mark_and_remove(tmp_path):
    df = tmp_path / "d.json"
    col = BookCollection(str(df))
    col.add_book("ToRead", "A", 2010)
    assert col.mark_as_read("ToRead") is True

    col2 = BookCollection(str(df))
    book = col2.find_book_by_title("ToRead")
    assert book is not None and book.read is True

    assert col.remove_book("ToRead") is True
    col3 = BookCollection(str(df))
    assert col3.find_book_by_title("ToRead") is None


def test_parse_bool():
    assert _parse_bool(True) is True
    assert _parse_bool(1) is True
    assert _parse_bool("yes") is True
    assert _parse_bool("no") is False
    assert _parse_bool(None) is False


def test_load_malformed_json(tmp_path):
    df = tmp_path / "d.json"
    df.write_text("not a json")
    col = BookCollection(str(df))
    assert col.list_books() == []
