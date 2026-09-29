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

## Usage — Quant formulas

```python
from fyrefly import si, ci, si_ci_diff, profit, loss, ap, gp, hp, avg, avgc, mode, median, hyp, slope, centroid, dist

# Interest
si(1000, 2, 5)                    # 100.0   (Simple Interest: p, n, r)
ci(1000, 2, 10)                   # 210.0   (Compound Interest, annual by default)
ci(1000, 2, 10, "semi-annual")    # 215.5   (compounded twice a year)
si_ci_diff(1000, 10, 2)           # 10.0    (CI - SI, supports n = 2 or 3 only)

# Profit / Loss — smart-detects if you called the wrong one
profit(120, 100)         # 20
profit(120, 100, "%")    # (20, 20.0)   value + percentage
loss(80, 100)             # 20
loss(80, 100, "%")        # (20, 20.0)
profit(80, 100)           # raises: "this is a LOSS, not a profit. Use loss(80, 100) instead."

# Sequences: AP, GP, HP
ap(2, 3, 4)          # [2, 5, 8, 11]        full sequence
ap.tn(2, 3, 4)       # 11                    nth term
ap.sn(2, 3, 4)       # 26.0                  sum of first n terms

gp(2, 3, 4)          # [2, 6, 18, 54]
gp.tn(2, 3, 4)       # 54
gp.sn(2, 3, 4)       # 80.0

hp(2, 3, 4)          # [2.0, 0.2857..., 0.1538..., 0.1052...]
hp.tn(2, 3, 4)       # 0.10526315789473684
hp.sn(2, 3, 4)       # 2.5448235974551765

# Averages, mode, median
avg(10, 12, 13)          # 11.666666666666666        plain average of individual numbers
avgc(5, 3, 10, 2)         # 7.0                        weighted avg from (value, count) pairs
mode(1, 1, 2, 2)          # [1, 2]
median(1, 2, 3, 4)        # 2.5

# Geometry
hyp(3, 4)                              # 5.0
slope((1, 2), (3, 4))                  # 1.0
centroid((1, 2), (3, 2), (4, 5))       # (2.6666666666666665, 3.0)
dist((6, 2), (10, 5))                  # 5.0
```

## Usage — Equations, logs, exponents, roots, trigonometry

```python
from fyrefly import eqn, log, exp, sqrt, curt, nroot, sin, cos, tan, cosec, sec, cot

# Linear systems — n equations, n unknowns. Each equation: (coefficients..., constant)
eqn.l((2, 3, 5), (7, 6, 10))                          # (x, y) solving 2x+3y=5, 7x+6y=10
eqn.l((1, 1, 1, 6), (2, -1, 1, 3), (1, 2, -1, 2))     # (a, b, c) — scales to any n unknowns

# Polynomial roots — any degree, plus sum/product of roots (Vieta's formulas)
eqn.q(1, 3, 4)              # roots of x^2 + 3x + 4 = 0
eqn.q(3, 4, 6, 9, 10)       # roots of 3x^4 + 4x^3 + 6x^2 + 9x + 10 = 0
eqn.q.sum(5, 2, 3)          # -0.4   sum of roots of 5x^2 + 2x + 3 = 0
eqn.q.mul(5, 2, 3)          # 0.6    product of roots

# Logs and exponents
log(math.e)          # 1.0   natural log by default
log(8, 2)             # 3.0   log base 2
exp(2, 5)             # 32    2 to the power 5
exp(2, -1)            # 0.5   negative exponents work too

# Roots
sqrt(16)              # 4.0
curt(27)              # 3.0
curt(-27)             # -3.0   odd roots of negative numbers work correctly
nroot(16, 2)          # 4.0    generic nth root

# Trigonometry — degrees by default, pass mode="rad" for radians
sin(30)               # 0.5
cos(60)               # 0.5
tan(45)               # 1.0
cosec(30)             # 2.0
sec(60)               # 2.0
cot(45)               # 1.0
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

Transient provider errors (rate limits, temporary server issues) are retried automatically with backoff before giving up.

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

viz(c)                                # auto -> correlation heatmap
viz(c, "department")                  # auto -> bar chart of counts
viz(c, "age")                         # auto -> histogram
viz(c, "age", "salary")               # auto -> scatter (both numeric)
viz(c, "department", "salary")        # auto -> bar (mixed types)
viz(c, "age", "salary", kind="scatter")
viz(c, "department", "salary", kind="box")
viz(c, "department", kind="pie")
viz(c, "date", "revenue", kind="line")
viz(c, kind="pairplot", hue="department")
viz(c, "department", "salary", kind="bar", save="chart.png")   # also saves a file
```

Supported chart types: `line`, `bar`, `barh`, `scatter`, `hist`, `box`, `violin`, `kde`, `pie`, `heatmap`, `pairplot`, `area`, plus `"auto"` which picks a sensible chart based on your data.

### Namespace-style shortcuts

Once exactly one DataFrame is loaded, you can also call chart types directly, without repeating the DataFrame each time:

```python
c = load("data.csv")

viz.bar("department", "salary")
viz.scatter("age", "salary")
viz.line("date", "revenue")
viz.box("department", "salary")
viz.violin("department", "salary")
viz.hist("age")              # single-column kinds take just x
viz.kde("salary")
viz.pie("department")
viz.heatmap()                # no columns needed
viz.pairplot(hue="department")   # no columns needed
```

If more than one DataFrame is loaded, the shortcut can't guess which one you mean — pass it explicitly as the first argument instead: `viz.bar(c, "department", "salary")`.

## Functions

| Function | Description | Needs API key? |
|---|---|---|
| `add(*nos)` | Adds all given numbers | No |
| `mul(*nos)` | Multiplies all given numbers | No |
| `div(*nos)` | Divides left to right: first ÷ second ÷ third ... | No |
| `mod(*nos)` | Finds remainder left to right: first % second % third ... | No |
| `diff(*nos)` | Subtracts left to right: first − second − third ... | No |
| `si(p, n, r)` | Simple Interest | No |
| `ci(p, n, r, freq)` | Compound Interest ("annual" or "semi-annual") | No |
| `si_ci_diff(p, r, n)` | CI − SI, for n = 2 or 3 years | No |
| `profit(sp, cp, "%")` | Profit value, or (value, %) if "%" passed — smart-detects a loss | No |
| `loss(sp, cp, "%")` | Loss value, or (value, %) if "%" passed — smart-detects a profit | No |
| `ap/.tn/.sn(a, d, n)` | Arithmetic Progression: sequence, nth term, sum of n terms | No |
| `gp/.tn/.sn(a, r, n)` | Geometric Progression: sequence, nth term, sum of n terms | No |
| `hp/.tn/.sn(a, d, n)` | Harmonic Progression: sequence, nth term, sum of n terms | No |
| `avg(*nos)` | Plain average of individual numbers | No |
| `avgc(*value_count_pairs)` | Weighted average from (value, count) pairs | No |
| `mode(*nos)` | Most frequent value(s) | No |
| `median(*nos)` | Median | No |
| `hyp(a, b)` | Hypotenuse of a right triangle | No |
| `slope(point1, point2)` | Slope between two (x, y) points | No |
| `centroid(p1, p2, p3)` | Centroid of a triangle from three (x, y) points | No |
| `dist(point1, point2)` | Distance between two (x, y) points | No |
| `eqn.l(*equations)` | Solves a system of n linear equations in n unknowns | No |
| `eqn.q(*coeffs)` | Roots of a polynomial of any degree | No |
| `eqn.q.sum(*coeffs)` / `eqn.q.mul(*coeffs)` | Sum / product of all roots (Vieta's formulas), any degree | No |
| `log(x, base=e)` | Logarithm, natural by default | No |
| `exp(a, b)` | a raised to the power b (positive or negative) | No |
| `sqrt(no)` / `curt(no)` / `nroot(no, n)` | Square root / cube root / generic nth root | No |
| `sin/cos/tan/cosec/sec/cot(angle, mode="deg")` | Trigonometric functions, degrees by default | No |
| `load(path)` | Loads a CSV/Excel/Google Sheet into a DataFrame and previews it | No |
| `loadh(df)` | Previews just the column headers | No |
| `loadc(df)` | Previews the record count | No |
| `loads(df)` | Previews the schema (columns + datatypes) | No |
| `sql(query)` | Runs any SQL query against a loaded DataFrame, by variable name | No |
| `xtract(df, filename=None)` | Exports a DataFrame to CSV in the current directory | No |
| `clean(df)` | Dedupes, strips whitespace, standardizes column names | No |
| `ask(data, question, api_key=...)` | Converts a plain-English question into SQL and runs it | **Yes** |
| `insights(df, api_key=...)` | Generates a plain-English summary of a dataset | **Yes** |
| `viz(df, x=None, y=None, kind="auto", ...)` | Visualizes a DataFrame — 12+ chart types | No |
| `viz.bar/.scatter/.line/.box/.violin/.hist/.kde/.pie/.heatmap/.pairplot` | Namespace shortcuts for each chart type — auto-detect the loaded DataFrame | No |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT