import pandas as pd

data = {
    "Name": ["John", "Anna", "Peter", "Linda"],
    "Age": [28, 34, 29, 42],
    "City": ["New York", "Paris", "Berlin", "London"],
    "Salary": [65000, 70000, 62000, 85000],
}
# Create a sample DataFrame
df = pd.DataFrame(data)
# Non existent column
df["NonExistentColumn"]  # <-- triggers an error

# Basic operations
print("\nSelect a column:")
print(df["Name"])

print("\nFilter rows where Age > 30:")
print(df[df["Age"] > 30])

# Group by and aggregate
print("\nAverage salary by city:")
grouped = df.groupby("City")["Salary"].mean()  # <- both City and Salary must be present
print(grouped)

# Add a new column
df["Bonus"] = df["Salary"] * 0.1  # <- Assigns a new column ("Bonus")
print("\nDataFrame with bonus column:")
print(df)

# Sort values
print("\nSorted by Age (descending):")
print(df.sort_values("Age", ascending=False))  # <- "Age" must be present

# Access new column
print("\nBonus column:")
print(df["Bonus"])


# Use assign
df = df.assign(
    YearlyBonus=lambda x: x["Bonus"] * 12  # <- Assigns a new column ("YearlyBonus")
)
print("\nDataFrame with yearly bonus column:")
print(df)
