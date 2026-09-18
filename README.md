# Fyrefly

Simple, flexible functions to add, multiply, and divide **any count of numbers**.

## Installation

```bash
pip install fyrefly
```

## Usage

```python
from fyrefly import add, mul, div

add(5, 4, 6, 10)     # 25
mul(5, 4, 6, 10)     # 1200
div(100, 5, 2)       # 10.0
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

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
