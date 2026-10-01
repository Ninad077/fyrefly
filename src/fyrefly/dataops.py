import os
import inspect
import pandas as pd
import duckdb



# Loads & previews the dataframe
def load(path):
    """
    Loads a CSV, Excel, or Google Sheet into a DataFrame and previews it.

    Examples:
        c = load("data.csv")
        c = load("data.xlsx")
        c = load("https://docs.google.com/spreadsheets/d/XXXX/edit#gid=0")
    """
    ext = os.path.splitext(path)[1].lower()

    if "docs.google.com/spreadsheets" in path:
        if "/edit" in path:
            base = path.split("/edit")[0]
        else:
            base = path.rstrip("/")
        gid = "0"
        if "gid=" in path:
            gid = path.split("gid=")[-1].split("&")[0]
        csv_url = f"{base}/export?format=csv&gid={gid}"
        df = pd.read_csv(csv_url)

    elif ext == ".csv":
        df = pd.read_csv(path)

    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)

    else:
        raise ValueError(f"Unsupported file type: '{ext}'. Use .csv, .xlsx, .xls, or a Google Sheet link.")

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns from '{path}'\n")
    print(df.head())
    return df

# Runs a SQL query on the previewed dataframe
def sql(query):
    """
    Runs ANY SQL query against DataFrames already loaded in your script
    (via load()), by name. Uses DuckDB under the hood, so full SQL is
    supported: WHERE, GROUP BY, JOIN, ORDER BY, window functions, etc.

    Example:
        c = load("data.csv")
        d = sql("select * from c where age > 30 order by age desc")
    """
    frame = inspect.currentframe().f_back
    caller_vars = {**frame.f_globals, **frame.f_locals}

    con = duckdb.connect()
    for name, val in caller_vars.items():
        if isinstance(val, pd.DataFrame):
            con.register(name, val)

    result = con.execute(query).df()
    print(f"Query returned {len(result)} rows, {len(result.columns)} columns\n")
    print(result.head())
    return result



# Helps user download the data
def xtract(df, filename=None):
    """
    Exports a DataFrame (usually the result of sql()) to a CSV file
    in the current working directory.

    Example:
        xtract(d)
        xtract(sql("select * from c"), filename="filtered.csv")
    """
    if filename is None:
        filename = "fyrefly_export.csv"

    path = os.path.join(os.getcwd(), filename)
    df.to_csv(path, index=False)
    print(f"Exported {len(df)} rows to: {path}")
    return path


#Helps user preview the headers of the dataframe
def loadh(df):
    """
    Previews just the column headers of a loaded DataFrame.

    Example:
        c = load("data.csv")
        loadh(c)
    """
    cols = list(df.columns)
    print(f"Headers ({len(cols)}):")
    for col in cols:
        print(f" - {col}")
    return cols


# Previews the record count of the loaded dataframe
def loadc(df):
    """
    Previews the record count (number of rows) of a loaded DataFrame.

    Example:
        c = load("data.csv")
        loadc(c)
    """
    count = len(df)
    print(f"Record count: {count}")
    return count



# Previews the schema of the loaded dataframe
def loads(df):
    """
    Previews the schema of a loaded DataFrame: each column and its datatype.

    Example:
        c = load("data.csv")
        loads(c)
    """
    schema = df.dtypes
    print("Schema:")
    print(schema)
    return schema

# Cleans the dataframe
def clean(df, lowercase_columns=True, strip_strings=True, drop_duplicates=True, drop_empty_rows=True):
    """
    Performs common cleanup on a DataFrame and previews what changed:
      - Standardizes column names (lowercase, spaces -> underscores)
      - Strips leading/trailing whitespace from text columns
      - Drops exact duplicate rows
      - Drops rows that are entirely empty (all NaN)

    Returns a NEW cleaned DataFrame (does not modify the original in place).

    Example:
        c = load("messy_data.csv")
        c = clean(c)
    """
    original_shape = df.shape
    df = df.copy()

    if lowercase_columns:
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    if strip_strings:
        str_cols = df.select_dtypes(include="object").columns
        for col in str_cols:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    duplicates_removed = 0
    if drop_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        duplicates_removed = before - len(df)

    empty_rows_removed = 0
    if drop_empty_rows:
        before = len(df)
        df = df.dropna(how="all")
        empty_rows_removed = before - len(df)

    print(f"Cleaned: {original_shape} -> {df.shape}")
    if lowercase_columns:
        print(" - Standardized column names (lowercase, underscores)")
    if strip_strings:
        print(" - Stripped whitespace from text columns")
    if duplicates_removed:
        print(f" - Removed {duplicates_removed} duplicate row(s)")
    if empty_rows_removed:
        print(f" - Removed {empty_rows_removed} fully empty row(s)")

    return df


# Internal helper: auto-detects the loaded DataFrame if not passed explicitly
def _resolve_single_df(df, frame):
    """Auto-detects the loaded DataFrame if df isn't given explicitly, same
    pattern used by viz's namespace methods. Requires exactly one DataFrame
    in scope when df=None."""
    if df is not None:
        return df
    caller_vars = {**frame.f_globals, **frame.f_locals}
    dfs = {name: val for name, val in caller_vars.items() if isinstance(val, pd.DataFrame)}
    if len(dfs) == 0:
        raise ValueError(
            "No DataFrame found. Load one first with load(), or pass it explicitly: "
            "vlook(value, return_col, df=your_df)"
        )
    if len(dfs) > 1:
        names = ", ".join(dfs.keys())
        raise ValueError(
            f"Multiple DataFrames found ({names}) — can't tell which to use. "
            f"Pass it explicitly: vlook(value, return_col, df=your_df)"
        )
    return next(iter(dfs.values()))


# Internal helper: resolves a column by name or position
def _get_column(df, col):
    """Resolves a column by name (string) or position (int), Excel-style."""
    if isinstance(col, int):
        return df.columns[col]
    return col


# Looks up a value in the first column, like Excel's VLOOKUP
def vlook(value, return_col, df=None, default="__RAISE__"):
    """
    Looks up `value` in the FIRST column of your data (like Excel's VLOOKUP)
    and returns the matching row's value from `return_col`.

    return_col can be a column name (string) or a 0-based column index (int).

    If exactly one DataFrame is loaded, df is auto-detected — no need to
    pass it. If you've loaded more than one, pass it explicitly: df=your_df.

    Raises a clear error if `value` isn't found, unless you pass default=...,
    in which case that's returned instead.

    Example:
        c = load("employees.csv")
        vlook("Alice", "salary")              # finds "Alice" in column 1
        vlook("Alice", "salary", default=0)   # returns 0 if not found
    """
    frame = inspect.currentframe().f_back
    df = _resolve_single_df(df, frame)

    lookup_col = df.columns[0]
    return_col_name = _get_column(df, return_col)

    matches = df[df[lookup_col] == value]
    if matches.empty:
        if default != "__RAISE__":
            return default
        raise ValueError(f"Value '{value}' not found in column '{lookup_col}'")
    return matches.iloc[0][return_col_name]


# Looks up a value in ANY column, like Excel's XLOOKUP
def xlook(value, lookup_col, return_col, df=None, default="__RAISE__"):
    """
    Looks up `value` in ANY column you specify (like Excel's XLOOKUP) and
    returns the matching row's value from `return_col`.

    lookup_col and return_col can be column names (strings) or 0-based
    column indices (ints).

    If exactly one DataFrame is loaded, df is auto-detected — no need to
    pass it. If you've loaded more than one, pass it explicitly: df=your_df.

    Raises a clear error if `value` isn't found, unless you pass default=...,
    in which case that's returned instead.

    Example:
        c = load("employees.csv")
        xlook("Alice", "name", "salary")              # lookup column can be anywhere
        xlook("Alice", "name", "salary", default=0)   # returns 0 if not found
    """
    frame = inspect.currentframe().f_back
    df = _resolve_single_df(df, frame)

    lookup_col_name = _get_column(df, lookup_col)
    return_col_name = _get_column(df, return_col)

    matches = df[df[lookup_col_name] == value]
    if matches.empty:
        if default != "__RAISE__":
            return default
        raise ValueError(f"Value '{value}' not found in column '{lookup_col_name}'")
    return matches.iloc[0][return_col_name]


# Counts rows matching a condition, like Excel's COUNTIF
def countif(col, value, df=None):
    """
    Counts rows where `col` equals `value` — like Excel's COUNTIF.

    If exactly one DataFrame is loaded, df is auto-detected. If you've
    loaded more than one, pass it explicitly: df=your_df.

    Example:
        c = load("employees.csv")
        countif("department", "Engineering")   # how many rows match
    """
    frame = inspect.currentframe().f_back
    df = _resolve_single_df(df, frame)
    return int((df[col] == value).sum())


# Sums a column for rows matching a condition, like Excel's SUMIF
def sumif(col, value, sum_col, df=None):
    """
    Sums `sum_col` for rows where `col` equals `value` — like Excel's SUMIF.

    If exactly one DataFrame is loaded, df is auto-detected. If you've
    loaded more than one, pass it explicitly: df=your_df.

    Example:
        c = load("employees.csv")
        sumif("department", "Engineering", "salary")   # total salary for that department
    """
    frame = inspect.currentframe().f_back
    df = _resolve_single_df(df, frame)
    return df.loc[df[col] == value, sum_col].sum()


# Averages a column for rows matching a condition, like Excel's AVERAGEIF
def avgif(col, value, avg_col, df=None):
    """
    Averages `avg_col` for rows where `col` equals `value` — like Excel's
    AVERAGEIF.

    If exactly one DataFrame is loaded, df is auto-detected. If you've
    loaded more than one, pass it explicitly: df=your_df.

    Example:
        c = load("employees.csv")
        avgif("department", "Engineering", "salary")   # average salary for that department
    """
    frame = inspect.currentframe().f_back
    df = _resolve_single_df(df, frame)
    matches = df.loc[df[col] == value, avg_col]
    if matches.empty:
        raise ValueError(f"No rows found where '{col}' equals '{value}'")
    return matches.mean()