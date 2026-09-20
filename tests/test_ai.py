from unittest.mock import patch
import pandas as pd
from fyrefly import ask, insights
from fyrefly.ai import _detect_provider, _clean_sql, _describe_schema


def _sample_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "Diana"],
        "department": ["Engineering", "Sales", "Engineering", "Marketing"],
        "salary": [85000, 62000, 95000, 58000],
    })


def test_detect_provider():
    assert _detect_provider("sk-ant-fakekey12345") == ("anthropic", None)
    assert _detect_provider("AIzaFakeKey12345") == ("gemini", None)
    assert _detect_provider("gsk_FakeKey12345") == ("openai_compatible", "https://api.groq.com/openai/v1")
    assert _detect_provider("sk-FakeOpenAIKey12345") == ("openai", None)


def test_detect_provider_unknown_format_raises():
    try:
        _detect_provider("totally-unknown-format")
        assert False, "should have raised"
    except ValueError:
        pass


def test_clean_sql_strips_markdown_and_labels():
    assert _clean_sql("```sql\nSELECT * FROM c;\n```") == "SELECT * FROM c"
    assert _clean_sql("SQL: select * from c") == "select * from c"
    assert _clean_sql("  select * from c  ") == "select * from c"


def test_describe_schema():
    c = _sample_df()
    description = _describe_schema({"c": c})
    assert "Table 'c'" in description
    assert "salary" in description


def test_ask_single_dataframe():
    c = _sample_df()
    with patch("fyrefly.ai._call_llm", return_value="select department, avg(salary) as avg_salary from c group by department"):
        result = ask(c, "average salary by department?", api_key="AIzaFakeKeyForTest")
    assert len(result) == 3
    assert "avg_salary" in result.columns


def test_ask_multiple_dataframes_join():
    sales = pd.DataFrame({"customer_id": [1, 2, 1, 3], "amount": [100, 200, 150, 300]})
    customers = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    query = (
        "select customers.name, sum(sales.amount) as total from sales "
        "join customers on sales.customer_id = customers.id group by customers.name"
    )
    with patch("fyrefly.ai._call_llm", return_value=query):
        result = ask((sales, customers), "top customers by total sales?", api_key="AIzaFakeKeyForTest")
    assert len(result) == 3
    assert "total" in result.columns


def test_ask_no_api_key_raises():
    c = _sample_df()
    try:
        ask(c, "average salary?", api_key=None)
        assert False, "should have raised without an API key or env var set"
    except ValueError:
        pass


def test_insights_returns_text():
    c = _sample_df()
    fake_summary = "This dataset has 4 employees across 3 departments with no missing values."
    with patch("fyrefly.ai._call_llm", return_value=fake_summary):
        summary = insights(c, api_key="AIzaFakeKeyForTest")
    assert summary == fake_summary