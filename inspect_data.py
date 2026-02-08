                                                                
import pandas as pd

try:
    df = pd.read_excel('input data.xlsx')
    print("Columns:", df.columns.tolist())
    print("Shape:", df.shape)
    print("First 5 rows:\n", df.head())
    print("Data Types:\n", df.dtypes)
except Exception as e:
    print(f"Error reading Excel file: {e}")
