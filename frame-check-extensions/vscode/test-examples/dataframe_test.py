"""
Test file for demonstrating Frame Check VS Code extension capabilities.

This file contains various DataFrame operations that should trigger
different types of errors and validations when using the Frame Check
language server.
"""

import numpy as np
import pandas as pd


# Example 1: Basic DataFrame with column access errors
def test_basic_dataframe():
    """Test basic DataFrame column access validation."""
    # Create a simple DataFrame
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["New York", "London", "Tokyo"],
        }
    )

    print(df["salary"])  # Error: Column 'salary' not found
    df['salary'] = [50000, 60000, 70000]  # Adding a new column

    print(df['salary'])

    return df


# Example 2: DataFrame with dynamic column creation
def test_dynamic_columns():
    """Test DataFrame with columns added dynamically."""
    df = pd.DataFrame({"a": [1, 2, 3]})

    # Add new column
    df["b"] = df["a"] * 2

    # Valid access after column creation
    print(df["b"])  # Should work

    # Invalid access
    print(df["c"])  # Error: Column 'c' not found

    return df


# Example 3: Multiple DataFrames
def test_multiple_dataframes():
    """Test handling of multiple DataFrames in the same scope."""
    df1 = pd.DataFrame({"user_id": [1, 2, 3], "username": ["alice", "bob", "charlie"]})

    df2 = pd.DataFrame(
        {
            "product_id": [101, 102, 103],
            "product_name": ["Widget A", "Widget B", "Widget C"],
            "price": [10.99, 15.99, 20.99],
        }
    )

    # Valid accesses
    print(df1["user_id"])
    print(df2["price"])

    # Invalid accesses - mixing up DataFrames
    print(df1["price"])  # Error: 'price' not in df1
    print(df2["username"])  # Error: 'username' not in df2

    return df1, df2


# Example 4: DataFrame from CSV (simulated)
def test_csv_dataframe():
    """Test DataFrame loaded from CSV with unknown columns."""
    # Simulate loading from CSV
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=5),
            "value": [10, 20, 30, 40, 50],
            "category": ["A", "B", "A", "C", "B"],
        }
    )

    # Valid operations
    print(df["timestamp"])
    result = df.groupby("category")["value"].sum()

    # Invalid operations
    print(df["amount"])  # Error: Column 'amount' not found
    print(df["status"])  # Error: Column 'status' not found

    return df


# Example 5: Complex DataFrame operations
def test_complex_operations():
    """Test complex DataFrame operations and method chaining."""
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=10),
            "sales": np.random.randint(100, 1000, 10),
            "region": np.random.choice(["North", "South", "East", "West"], 10),
        }
    )

    # Valid complex operations
    monthly_sales = df.groupby("region")["sales"].sum()
    filtered_df = df[df["sales"] > 500]

    # Invalid column in filtering
    high_profit = df[df["profit"] > 100]  # Error: 'profit' column doesn't exist

    # Invalid column in groupby
    region_profit = df.groupby("region")["profit"].mean()  # Error: 'profit' not found

    return df


# Example 6: DataFrame with index operations
def test_index_operations():
    """Test DataFrame index and column operations."""
    df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"], "score": [85, 92, 78]})

    # Set index
    df_indexed = df.set_index("name")

    # Valid operations
    print(df_indexed["score"])
    print(df_indexed.loc["Alice"])

    # Invalid operations
    print(df_indexed["grade"])  # Error: 'grade' column doesn't exist

    return df_indexed


# Example 7: DataFrame with missing value handling
def test_missing_values():
    """Test DataFrame operations with missing values."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["Alice", "Bob", None, "David"],
            "age": [25, None, 30, 35],
        }
    )

    # Valid operations
    df_clean = df.dropna(subset=["name"])
    df_filled = df.fillna({"age": 0})

    # Invalid column operations
    df_invalid = df.dropna(subset=["salary"])  # Error: 'salary' not found

    return df


# Example 8: DataFrame concatenation and merging
def test_dataframe_operations():
    """Test DataFrame concatenation and merging operations."""
    df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    df2 = pd.DataFrame({"id": [1, 2], "age": [25, 30]})

    # Valid merge
    merged = pd.merge(df1, df2, on="id")
    print(merged["name"])  # Should work after merge
    print(merged["age"])  # Should work after merge

    # Invalid access before considering merge result
    print(df1["age"])  # Error: 'age' not in df1

    return merged


if __name__ == "__main__":
    # Run all test functions
    print("Testing Frame Check VS Code Extension...")

    test_basic_dataframe()
    test_dynamic_columns()
    test_multiple_dataframes()
    test_csv_dataframe()
    test_complex_operations()
    test_index_operations()
    test_missing_values()
    test_dataframe_operations()

    print("Test file execution complete!")

# Exclude from pytest collection
__test__ = False