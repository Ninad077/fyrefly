import os
import matplotlib
matplotlib.use("Agg")  # safe default for headless environments; interactive use still works via plt.show()
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


def viz(df, kind="auto", x=None, y=None, hue=None, title=None, figsize=(8, 5), save=None, **kwargs):
    """
    Visualizes a DataFrame — covers the major chart types built on
    matplotlib/seaborn: line, bar, barh, scatter, hist, box, violin,
    kde, pie, heatmap (correlation), pairplot, area.

    kind="auto" (default) picks a sensible chart based on what you pass:
      - no x, no y            -> correlation heatmap of numeric columns
      - x only, numeric       -> histogram
      - x only, categorical   -> bar chart of value counts
      - x and y, both numeric -> scatter plot
      - x and y, mixed types  -> bar chart (y aggregated by x)

    Examples:
        viz(c)                                    # auto: correlation heatmap
        viz(c, x="department")                    # auto: bar chart of counts
        viz(c, x="age")                            # auto: histogram
        viz(c, kind="scatter", x="age", y="salary")
        viz(c, kind="bar", x="department", y="salary")
        viz(c, kind="box", x="department", y="salary")
        viz(c, kind="pie", x="department")
        viz(c, kind="line", x="date", y="revenue")
        viz(c, kind="pairplot", hue="department")
        viz(c, save="chart.png")                  # also saves to current directory

    Any extra keyword arguments are passed through to the underlying
    matplotlib/seaborn plotting call for fine-tuning.
    """
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