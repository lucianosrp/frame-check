> [!WARNING]
> This project is currently under active development and is not considered polished. You are welcome to fork it, contribute to making it more stable, or raise issues.
---

# frame-check
A type checker for dataframes!

## Why frame-check?
Have you ever tried to access a column but not been entirely sure if that column exists?

```python
df.col_a
df["col_a"]
```

Currently, you have two options:

1. Manually trace every reference to `df` to verify if "col_a" was assigned to the dataframe or if "col_a" is part of the original data source.

2. Dynamically inspect the dataframe by running additional code:
```pycon
>>> df.columns
Index(['col_a', 'col_b', 'col_c'], dtype='object')
```
If you don't follow one of these two options, your code may break at runtime.

What if there was a tool such as `mypy` that would allow you to keep track of the dataframe's schema and warn you (*before your code crashes*) if you are trying to access a column that does not exits.

```

line[32]: TypeError: df["col_a"]
                     ^^^^^^^^^^
                    Column 'col_a' does not exist in the dataframe schema.
                    dataframe (df) was defined at line[10]:

                    |10  df = pd.DataFrame({         <- here
                         --
                    |11      "col_b": [4, 5, 6],
                    |12      "col_c": [7, 8, 9]
                    |13  })

                    At this stage (line[32]), it has the following columns:
                    - col_b
                    - col_c

```

Introducing, `frame-check` - your static dataframe companion



### Existing research/ solutions

- [pdchecker](https://github.com/ncu-psl/pdchecker)
- [Mypy issue](https://github.com/python/mypy/issues/17935)
