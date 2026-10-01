import os
import pandas as pd
import pytest
from fyrefly import load, loadh, loadc, loads, sql, xtract, clean, vlook, xlook, countif, sumif, avgif


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


def _sample_lookup_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "department": ["Engineering", "Sales", "Marketing"],
        "salary": [85000, 62000, 95000],
    })


def test_vlook_auto_detects_single_df():
    c = _sample_lookup_df()
    assert vlook("Alice", "salary") == 85000
    assert vlook("Bob", "department") == "Sales"


def test_vlook_return_col_by_index():
    c = _sample_lookup_df()
    assert vlook("Charlie", 2) == 95000


def test_vlook_not_found_raises():
    c = _sample_lookup_df()
    with pytest.raises(ValueError):
        vlook("Zoe", "salary")


def test_vlook_not_found_returns_default():
    c = _sample_lookup_df()
    assert vlook("Zoe", "salary", default=0) == 0


def test_vlook_explicit_df():
    c = _sample_lookup_df()
    assert vlook("Alice", "salary", df=c) == 85000


def test_xlook_searches_any_column():
    c = _sample_lookup_df()
    assert xlook("Engineering", "department", "name") == "Alice"
    assert xlook(95000, "salary", "name") == "Charlie"


def test_xlook_not_found_returns_default():
    c = _sample_lookup_df()
    assert xlook("Nonexistent", "department", "name", default="N/A") == "N/A"


def test_lookup_ambiguous_multiple_dataframes_raises():
    c = _sample_lookup_df()
    d = _sample_lookup_df()
    with pytest.raises(ValueError, match="Multiple DataFrames"):
        vlook("Alice", "salary")


def _sample_countif_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "Diana", "Ethan"],
        "department": ["Engineering", "Sales", "Engineering", "Marketing", "Engineering"],
        "salary": [85000, 62000, 95000, 58000, 70000],
    })


def test_countif():
    c = _sample_countif_df()
    assert countif("department", "Engineering") == 3


def test_countif_no_matches():
    c = _sample_countif_df()
    assert countif("department", "Nonexistent") == 0


def test_sumif():
    c = _sample_countif_df()
    assert sumif("department", "Engineering", "salary") == 250000


def test_avgif():
    c = _sample_countif_df()
    assert abs(avgif("department", "Engineering", "salary") - 83333.33333333333) < 1e-6


def test_avgif_no_matches_raises():
    c = _sample_countif_df()
    with pytest.raises(ValueError):
        avgif("department", "Nonexistent", "salary")


def test_countif_explicit_df():
    c = _sample_countif_df()
    d = pd.DataFrame({"department": ["Sales", "Sales"]})
    assert countif("department", "Sales", df=d) == 2