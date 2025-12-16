# Supported Features

### dataframe_creation_methods

| id                        | title                | code                                                           | description                                                                                                                                                                           | supported   |
|:--------------------------|:---------------------|:---------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|
| <a id="DCMS-1"></a>DCMS-1 | Dictionary Of Lists  | pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})                 | Creates a DataFrame from a dictionary where keys become column names and list values become the data for each column. This is fully supported in frame-check as the primary use case. | ✅          |
| <a id="DCMS-2"></a>DCMS-2 | List Of Dictionaries | pd.DataFrame([{'col1': 1, 'col2': 3}, {'col1': 2, 'col2': 4}]) | Creates a DataFrame where each dictionary represents a row, with keys as column names.                                                                                                | ✅          |
| <a id="DCMS-6"></a>DCMS-6 | From Csv             | pd.read_csv('file.csv', usecols=["a","b"])                     | Loads data from a CSV file into a DataFrame.                                                                                                                                          | ✅          |

### column_assignment_methods

| id                        | title             | code                                       | description                                                                                                 | supported   |
|:--------------------------|:------------------|:-------------------------------------------|:------------------------------------------------------------------------------------------------------------|:------------|
| <a id="CAM-1"></a>CAM-1   | Direct Assignment | df["c"] = [7, 8, 9]                        | The most common method for assigning values to a column. If the column doesn't exist, it creates a new one. | ✅          |
| <a id="CAM-7"></a>CAM-7   | Assign Method     | df = df.assign(A=[1, 2, 3])                | Returns a new DataFrame with the column added or modified. Great for method chaining.                       | ✅          |
| <a id="CAM-9"></a>CAM-9   | Insert Method     | df.insert(0, "A", [1, 2, 3])               | Inserts a column at a specific position in the DataFrame. Modifies in place.                                | ❌          |
| <a id="CAM-10"></a>CAM-10 | Setitem With List | df[["c", "d"]] = [[7, 8, 9], [10, 11, 12]] | Assigns multiple columns at once, either from other columns or external values.                             | ✅          |


----
