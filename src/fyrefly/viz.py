import os
import inspect
import matplotlib
# matplotlib.use("Agg")  # safe default for headless environments; interactive use still works via plt.show()
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


_VALID_KINDS = (
    "auto", "line", "bar", "barh", "scatter", "hist", "box", "violin",
    "kde", "pie", "heatmap", "pairplot", "area",
)


def _pick_auto_kind(df, x, y):
    """Chooses a sensible chart type based on the given columns and their dtypes."""
    if x is None and y is None:
        return "heatmap"

    if x is not None and y is not None:
        x_numeric = pd.api.types.is_numeric_dtype(df[x])
        y_numeric = pd.api.types.is_numeric_dtype(df[y])
        if x_numeric and y_numeric:
            return "scatter"
        return "bar"

    col = x if x is not None else y
    if pd.api.types.is_numeric_dtype(df[col]):
        return "hist"
    return "bar"


def _render(df, kind, x=None, y=None, hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
    """Core rendering logic, shared by the callable viz(...) and every viz.<kind>(...) method."""
    if kind not in _VALID_KINDS:
        raise ValueError(f"Unknown kind '{kind}'. Supported: {', '.join(_VALID_KINDS)}")

    if kind == "auto":
        kind = _pick_auto_kind(df, x, y)
        print(f"Auto-selected chart type: {kind}")

    if kind == "pairplot":
        grid = sns.pairplot(df, hue=hue, **kwargs)
        if title:
            grid.fig.suptitle(title, y=1.02)
        fig = grid.fig
    else:
        fig, ax = plt.subplots(figsize=figsize)

        if kind == "line":
            df.plot(x=x, y=y, kind="line", ax=ax, **kwargs)
        elif kind == "area":
            df.plot(x=x, y=y, kind="area", ax=ax, **kwargs)
        elif kind == "bar":
            if x is not None and y is not None:
                sns.barplot(data=df, x=x, y=y, hue=hue, ax=ax, **kwargs)
            elif x is not None:
                df[x].value_counts().plot(kind="bar", ax=ax, **kwargs)
            else:
                raise ValueError("kind='bar' needs at least x=... (and optionally y=...)")
        elif kind == "barh":
            if x is not None:
                df[x].value_counts().plot(kind="barh", ax=ax, **kwargs)
            else:
                raise ValueError("kind='barh' needs x=...")
        elif kind == "scatter":
            if x is None or y is None:
                raise ValueError("kind='scatter' needs both x=... and y=...")
            sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax, **kwargs)
        elif kind == "hist":
            col = x if x is not None else y
            if col is None:
                raise ValueError("kind='hist' needs x=... (or y=...)")
            sns.histplot(data=df, x=col, hue=hue, ax=ax, **kwargs)
        elif kind == "box":
            sns.boxplot(data=df, x=x, y=y, hue=hue, ax=ax, **kwargs)
        elif kind == "violin":
            sns.violinplot(data=df, x=x, y=y, hue=hue, ax=ax, **kwargs)
        elif kind == "kde":
            col = x if x is not None else y
            if col is None:
                raise ValueError("kind='kde' needs x=... (or y=...)")
            sns.kdeplot(data=df, x=col, hue=hue, ax=ax, **kwargs)
        elif kind == "pie":
            if x is None:
                raise ValueError("kind='pie' needs x=...")
            df[x].value_counts().plot(kind="pie", ax=ax, autopct="%1.1f%%", **kwargs)
            ax.set_ylabel("")
        elif kind == "heatmap":
            numeric_df = df.select_dtypes(include="number")
            if numeric_df.shape[1] < 2:
                raise ValueError("kind='heatmap' needs at least 2 numeric columns for a correlation matrix.")
            sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax, **kwargs)

        if title:
            ax.set_title(title)

    plt.tight_layout()

    if save:
        path = os.path.join(os.getcwd(), save)
        fig.savefig(path, dpi=150, bbox_inches="tight")
        print(f"Saved chart to: {path}")

    plt.show()
    return fig


class Viz:
    """
    Visualizes DataFrames — callable directly (viz(df, kind=..., x=..., y=...))
    or via per-chart-type methods (viz.bar(x, y), viz.scatter(x, y), etc.).

    The per-chart-type methods DON'T take a df argument — they auto-detect
    the DataFrame already loaded in your script (e.g. via load()). This
    only works cleanly when exactly one DataFrame is in scope; if there
    are zero or more than one, you'll get a clear error telling you to
    either load just one dataset, or fall back to the explicit form:
    viz(df, kind="bar", x=..., y=...).

    Examples:
        c = load("data.csv")

        viz.bar("department", "salary")
        viz.scatter("age", "salary")
        viz.line("date", "revenue")
        viz.box("department", "salary")
        viz.hist("age")                 # single-column kinds take just x
        viz.pie("department")
        viz.kde("salary")
        viz.heatmap()                   # no columns needed
        viz.pairplot(hue="department")  # no columns needed

        # The original explicit form still works too:
        viz(c, kind="bar", x="department", y="salary")
    """

    def __call__(self, df, x=None, y=None, kind="auto", hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
        return _render(df, kind, x=x, y=y, hue=hue, title=title, figsize=figsize, save=save, **kwargs)

    def _auto_detect_df(self, frame):
        caller_vars = {**frame.f_globals, **frame.f_locals}
        dfs = {name: val for name, val in caller_vars.items() if isinstance(val, pd.DataFrame)}
        if len(dfs) == 0:
            raise ValueError(
                "No DataFrame found in scope. Load one first with load(), "
                "or pass it explicitly: viz(df, kind=\"bar\", x=..., y=...)"
            )
        if len(dfs) > 1:
            names = ", ".join(dfs.keys())
            raise ValueError(
                f"Multiple DataFrames found ({names}) — can't tell which to use. "
                f"Use the explicit form instead: viz(your_df, kind=\"bar\", x=..., y=...)"
            )
        return next(iter(dfs.values()))

    def _resolve_xy(self, frame, args):
        """For two-column chart types: bar, scatter, line, area, box, violin."""
        if args and isinstance(args[0], pd.DataFrame):
            df = args[0]
            rest = args[1:]
        else:
            df = self._auto_detect_df(frame)
            rest = args
        x = rest[0] if len(rest) >= 1 else None
        y = rest[1] if len(rest) >= 2 else None
        return df, x, y

    def _resolve_single(self, frame, args):
        """For single-column chart types: hist, kde, pie."""
        if args and isinstance(args[0], pd.DataFrame):
            df = args[0]
            rest = args[1:]
        else:
            df = self._auto_detect_df(frame)
            rest = args
        col = rest[0] if len(rest) >= 1 else None
        return df, col

    def _resolve_df_only(self, frame, args):
        """For chart types needing no columns: heatmap, pairplot."""
        if args and isinstance(args[0], pd.DataFrame):
            return args[0]
        return self._auto_detect_df(frame)

    def bar(self, *args, hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
        df, x, y = self._resolve_xy(inspect.currentframe().f_back, args)
        return _render(df, "bar", x=x, y=y, hue=hue, title=title, figsize=figsize, save=save, **kwargs)

    def barh(self, *args, title=None, figsize=(8, 5), save=None, **kwargs):
        df, x, _ = self._resolve_xy(inspect.currentframe().f_back, args)
        return _render(df, "barh", x=x, title=title, figsize=figsize, save=save, **kwargs)

    def scatter(self, *args, hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
        df, x, y = self._resolve_xy(inspect.currentframe().f_back, args)
        return _render(df, "scatter", x=x, y=y, hue=hue, title=title, figsize=figsize, save=save, **kwargs)

    def line(self, *args, title=None, figsize=(8, 5), save=None, **kwargs):
        df, x, y = self._resolve_xy(inspect.currentframe().f_back, args)
        return _render(df, "line", x=x, y=y, title=title, figsize=figsize, save=save, **kwargs)

    def area(self, *args, title=None, figsize=(8, 5), save=None, **kwargs):
        df, x, y = self._resolve_xy(inspect.currentframe().f_back, args)
        return _render(df, "area", x=x, y=y, title=title, figsize=figsize, save=save, **kwargs)

    def box(self, *args, hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
        df, x, y = self._resolve_xy(inspect.currentframe().f_back, args)
        return _render(df, "box", x=x, y=y, hue=hue, title=title, figsize=figsize, save=save, **kwargs)

    def violin(self, *args, hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
        df, x, y = self._resolve_xy(inspect.currentframe().f_back, args)
        return _render(df, "violin", x=x, y=y, hue=hue, title=title, figsize=figsize, save=save, **kwargs)

    def hist(self, *args, hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
        df, col = self._resolve_single(inspect.currentframe().f_back, args)
        return _render(df, "hist", x=col, hue=hue, title=title, figsize=figsize, save=save, **kwargs)

    def kde(self, *args, hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
        df, col = self._resolve_single(inspect.currentframe().f_back, args)
        return _render(df, "kde", x=col, hue=hue, title=title, figsize=figsize, save=save, **kwargs)

    def pie(self, *args, title=None, figsize=(8, 5), save=None, **kwargs):
        df, col = self._resolve_single(inspect.currentframe().f_back, args)
        return _render(df, "pie", x=col, title=title, figsize=figsize, save=save, **kwargs)

    def heatmap(self, *args, title=None, figsize=(8, 5), save=None, **kwargs):
        df = self._resolve_df_only(inspect.currentframe().f_back, args)
        return _render(df, "heatmap", title=title, figsize=figsize, save=save, **kwargs)

    def pairplot(self, *args, hue=None, title=None, save=None, **kwargs):
        df = self._resolve_df_only(inspect.currentframe().f_back, args)
        return _render(df, "pairplot", hue=hue, title=title, save=save, **kwargs)


viz = Viz()