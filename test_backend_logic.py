
import sys
import os
import pandas as pd

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.loader import DataLoader
from src.distributor import Distributor
from src.exporter import Exporter

def test_logic():
    print("Testing Backend Logic...")
    
    # 1. Load
    input_path = os.path.join("data", "input data.xlsx")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        return

    loader = DataLoader(input_path)
    try:
        original_df, processed_df = loader.load()
        print(f"Loaded {len(processed_df)} rows.")
        # Check Faculty Child detection
        fc_count = processed_df['is_faculty_child'].sum()
        print(f"Faculty Children detected: {fc_count}")
        if 'notes' in processed_df.columns:
             print("Sample Notes:", processed_df['notes'].unique())
    except Exception as e:
        print(f"Loader Error: {e}")
        return

    # 2. Distribute (AUTO Mode)
    distributor = Distributor(processed_df)
    distributor.calculate_capacities('AUTO')
    
    print("\nCapacities (Auto):", distributor.capacities)
    
    results = distributor.distribute()
    
    assigned = len([v for v in results.values() if v])
    print(f"\nAssigned: {assigned}/{len(processed_df)}")
    
    # 3. Export
    try:
        Exporter.export(original_df, results, 'output_final_test.xlsx')
        print("Export successful to output_final_test.xlsx")
    except Exception as e:
        print(f"Export Error: {e}")

    # Verify Export
    df_out = pd.read_excel('output_final_test.xlsx')
    if 'القسم المقبول' in df_out.columns:
        print("\nVerifying Output Column 'القسم المقبول':")
        print(df_out['القسم المقبول'].value_counts())
    else:
        print("\nError: Output column missing!")

if __name__ == "__main__":
    test_logic()
