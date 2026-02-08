
import pandas as pd

try:
    df = pd.read_excel('output_test.xlsx')
    # Filter to show relevant result columns
    cols_to_show = ['اسم الطالب', 'المجموع', 'قناة القبول', 'القسم المقبول', 'حالة القبول', 'تسلسل الرغبة']
    print(df[cols_to_show].head(10).to_string())
    print("\nTotal Rows:", len(df))
    print("\nCounts by Status:")
    print(df['حالة القبول'].value_counts())
except Exception as e:
    print(f"Error: {e}")
