# Fyrefly

A quant-based library to compute mathematical operations and run SQL queries on your data.

## Installation

```bash
pip install fyrefly
```

## Usage — Math functions

```python
from fyrefly import add, mul, div, mod

add(5, 4, 6, 10)     # 25
mul(5, 4, 6, 10)     # 1200
div(100, 5, 2)       # 10.0
mod(17, 5)           # 2
```

Each function accepts any number of arguments:

```python
add(1)                # 1
add(1, 2, 3, 4, 5)    # 15
mul()                  # 1 (identity)
```

## Usage — Data functions

```python
from fyrefly import load, loadh, loadc, loads, sql, xtract

c = load("data.csv")                 # loads a CSV/Excel/Google Sheet, previews it
loadh(c)                             # preview column headers
loadc(c)                             # preview record count
loads(c)                             # preview schema (columns + datatypes)

d = sql("select * from c where age > 30")   # run ANY SQL query on loaded data
xtract(d)                                    # export the result to CSV
xtract(sql("select * from c"), filename="all.csv")  # chained form also works
```

## Functions

| Function | Description |
|---|---|
| `add(*nos)` | Adds all given numbers |
| `mul(*nos)` | Multiplies all given numbers |
| `div(*nos)` | Divides left to right: first ÷ second ÷ third ... |
| `mod(*nos)` | Finds remainder left to right: first % second % third ... |
| `load(path)` | Loads a CSV/Excel/Google Sheet into a DataFrame and previews it |
| `loadh(df)` | Previews just the column headers |
| `loadc(df)` | Previews the record count |
| `loads(df)` | Previews the schema (columns + datatypes) |
| `sql(query)` | Runs any SQL query against a loaded DataFrame, by variable name |
| `xtract(df, filename=None)` | Exports a DataFrame to CSV in the current directory |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT