# Fyrefly

A Quant based library to compute mathematical operations.

## Installation

```bash
pip install fyrefly
```

## Usage

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

## Functions

| Function | Description |
|---|---|
| `add(*nos)` | Adds all given numbers |
| `mul(*nos)` | Multiplies all given numbers |
| `div(*nos)` | Divides left to right: first ÷ second ÷ third ... |
| `mod(*nos)` | Finds remainder left to right: first % second % third ... |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT