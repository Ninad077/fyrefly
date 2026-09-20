# Fyrefly

A quant-based library to compute mathematical operations, run SQL queries, get AI-powered insights, and visualize your data.

## Installation

```bash
pip install fyrefly
```

## Usage — Math functions

```python
from fyrefly import add, mul, div, mod, diff

add(5, 4, 6, 10)     # 25
mul(5, 4, 6, 10)     # 1200
div(100, 5, 2)       # 10.0
mod(17, 5)           # 2
diff(10, 3, 2)       # 5
```

Each function accepts any number of arguments:

```python
add(1)                # 1
add(1, 2, 3, 4, 5)    # 15
mul()                  # 1 (identity)
diff(10, 3)            # 7
```

## Usage — Data functions

```python
from fyrefly import load, loadh, loadc, loads, sql, xtract, clean

c = load("data.csv")                 # loads a CSV/Excel/Google Sheet, previews it
loadh(c)                             # preview column headers
loadc(c)                             # preview record count
loads(c)                             # preview schema (columns + datatypes)

c = clean(c)                         # dedupe, strip whitespace, standardize column names

d = sql("select * from c where age > 30")   # run ANY SQL query on loaded data
xtract(d)                                    # export the result to CSV
xtract(sql("select * from c"), filename="all.csv")  # chained form also works
```

**Note:** for Google Sheets, the sheet must be shared as "Anyone with the link – Viewer" for `load()` to access it.

## Usage — AI functions (require an API key)

```python
from fyrefly import ask, insights

c = load("sales.csv")

# Ask questions in plain English — converted to SQL and run automatically
ask(c, "what were total sales by region last quarter?", api_key="AIza...")

# Query across multiple datasets (e.g. a join) — scales to any count
ask((c, d), "who are our top customers by total sales?", api_key="AIza...")
ask((c, d, e), "...", api_key="AIza...")

# Get a plain-English summary of a dataset
insights(c, api_key="AIza...")
```

The provider (Anthropic, OpenAI, Gemini, or any OpenAI-compatible API like Groq/Mistral) is **auto-detected from your API key's format** — you usually don't need to specify it. API keys can also be set via environment variables instead of passing them directly: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`.

⚠️ **Never commit an API key into a script you push to GitHub.** Use an environment variable instead:
```bash
export GEMINI_API_KEY="AIza..."
```
```python
ask(c, "what were total sales by region?")   # picked up automatically from the env var
```

## Usage — Visualization (no AI, no API key needed)

```python
from fyrefly import viz

viz(c)                                          # auto -> correlation heatmap
viz(c, x="department")                          # auto -> bar chart of counts
viz(c, x="age")                                 # auto -> histogram
viz(c, kind="scatter", x="age", y="salary")
viz(c, kind="box", x="department", y="salary")
viz(c, kind="pie", x="department")
viz(c, kind="line", x="date", y="revenue")
viz(c, kind="pairplot", hue="department")
viz(c, kind="bar", x="department", y="salary", save="chart.png")   # also saves a file
```

Supported chart types: `line`, `bar`, `barh`, `scatter`, `hist`, `box`, `violin`, `kde`, `pie`, `heatmap`, `pairplot`, `area`, plus `"auto"` which picks a sensible chart based on your data.

## Functions

| Function | Description | Needs API key? |
|---|---|---|
| `add(*nos)` | Adds all given numbers | No |
| `mul(*nos)` | Multiplies all given numbers | No |
| `div(*nos)` | Divides left to right: first ÷ second ÷ third ... | No |
| `mod(*nos)` | Finds remainder left to right: first % second % third ... | No |
| `diff(*nos)` | Subtracts left to right: first − second − third ... | No |
| `load(path)` | Loads a CSV/Excel/Google Sheet into a DataFrame and previews it | No |
| `loadh(df)` | Previews just the column headers | No |
| `loadc(df)` | Previews the record count | No |
| `loads(df)` | Previews the schema (columns + datatypes) | No |
| `sql(query)` | Runs any SQL query against a loaded DataFrame, by variable name | No |
| `xtract(df, filename=None)` | Exports a DataFrame to CSV in the current directory | No |
| `clean(df)` | Dedupes, strips whitespace, standardizes column names | No |
| `ask(data, question, api_key=...)` | Converts a plain-English question into SQL and runs it | **Yes** |
| `insights(df, api_key=...)` | Generates a plain-English summary of a dataset | **Yes** |
| `viz(df, kind="auto", ...)` | Visualizes a DataFrame — 12+ chart types | No |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT