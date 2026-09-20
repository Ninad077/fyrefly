import os
import pandas as pd
from fyrefly import load, loadh, loadc, loads, sql, xtract, clean


def _make_sample_csv(tmp_path):
    csv_path = tmp_path / "sample.csv"
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [29, 34, 41],
        "salary": [85000, 62000, 95000],
    })
    df.to_csv(csv_path, index=False)
    return str(csv_path)


def test_load(tmp_path):
    path = _make_sample_csv(tmp_path)
    c = load(path)
    assert len(c) == 3
    assert list(c.columns) == ["name", "age", "salary"]


def test_loadh(tmp_path):
    c = load(_make_sample_csv(tmp_path))
    headers = loadh(c)
    assert headers == ["name", "age", "salary"]


def test_loadc(tmp_path):
    c = load(_make_sample_csv(tmp_path))
    assert loadc(c) == 3


def test_loads(tmp_path):
    c = load(_make_sample_csv(tmp_path))
    schema = loads(c)
    assert "salary" in schema.index


def test_sql(tmp_path):
    c = load(_make_sample_csv(tmp_path))
    d = sql("select * from c where salary > 70000")
    assert len(d) == 2


def test_xtract(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = load(_make_sample_csv(tmp_path))
    d = sql("select * from c where salary > 70000")
    out_path = xtract(d, filename="output.csv")
    assert os.path.exists(out_path)


def test_clean_strips_and_dedupes():
    messy = pd.DataFrame({
        " Name ": ["  Alice ", "Bob", "Bob", None],
        "Department": ["Engineering ", " Sales", " Sales", None],
        "Salary": [85000, 62000, 62000, None],
    })
    cleaned = clean(messy)
    assert list(cleaned.columns) == ["name", "department", "salary"]
    assert len(cleaned) == 2
    assert cleaned.iloc[0]["name"] == "Alice"
    assert cleaned.iloc[0]["department"] == "Engineering"