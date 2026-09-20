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