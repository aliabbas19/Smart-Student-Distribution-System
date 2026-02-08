import pandas as pd
import os

class DataLoader:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        try:
            df = pd.read_excel(self.file_path)
            # Clean column names
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            raise Exception(f"Error loading data: {e}")

    def get_student_choices(self, df):
        # Extract unique departments from choices
        choices = set()
        for col in ['الاختيار الأول', 'الاختيار الثاني', 'الاختيار الثالث']:
            if col in df.columns:
                choices.update(df[col].dropna().unique())
        return list(choices)
