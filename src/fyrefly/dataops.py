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