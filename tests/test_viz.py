import os
import pandas as pd
import numpy as np
from fyrefly import viz


def _sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "department": np.random.choice(["Engineering", "Sales", "Marketing"], 50),
        "age": np.random.randint(22, 60, 50),
        "salary": np.random.randint(40000, 150000, 50),
    })


def test_viz_auto_heatmap(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz(c, save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_auto_bar_for_categorical(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz(c, x="department", save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_scatter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz(c, kind="scatter", x="age", y="salary", save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_box(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz(c, kind="box", x="department", y="salary", save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_pie(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz(c, kind="pie", x="department", save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_invalid_kind_raises():
    c = _sample_df()
    try:
        viz(c, kind="not_a_real_chart")
        assert False, "should have raised"
    except ValueError:
        pass


def test_viz_scatter_missing_y_raises():
    c = _sample_df()
    try:
        viz(c, kind="scatter", x="age")
        assert False, "should have raised without y"
    except ValueError:
        pass


def test_viz_positional_xy_auto_picks_bar():
    c = _sample_df()
    fig = viz(c, "department", "salary")
    assert fig is not None


def test_viz_positional_xy_auto_picks_scatter():
    c = _sample_df()
    fig = viz(c, "age", "salary")
    assert fig is not None


def test_viz_namespace_bar_auto_detects_single_dataframe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz.bar("department", "salary", save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_namespace_scatter_auto_detects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz.scatter("age", "salary", save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_namespace_hist_single_column(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz.hist("age", save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_namespace_heatmap_no_columns_needed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz.heatmap(save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_namespace_explicit_df_overrides_autodetect(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = _sample_df()
    viz.bar(c, "department", "salary", save="chart.png")
    assert os.path.exists("chart.png")


def test_viz_namespace_scatter_missing_args_raises():
    c = _sample_df()
    try:
        viz.scatter()
        assert False, "should have raised without x and y"
    except ValueError:
        pass


def test_viz_namespace_ambiguous_multiple_dataframes_raises():
    c = _sample_df()
    d = _sample_df()
    try:
        viz.bar("department", "salary")
        assert False, "should have raised with multiple DataFrames in scope"
    except ValueError as e:
        assert "Multiple DataFrames" in str(e)