
"""
-----------------------------------------------------------
Smart Student Distribution System (S.S.D.S)
Copyright (C) 2026 Ali Abbas & Ali Alaa. All Rights Reserved.
Proprietary and confidential.
-----------------------------------------------------------
"""

import sys
import os
from src.loader import DataLoader
from src.distributor import Distributor
from src.exporter import Exporter

def main():
    print("="*60)
    print("🎓 Smart Student Distribution System (S.S.D.S)")
    print("   Version 2.0 - Senior Architecture Edition")
    print("="*60)

    # 1. Inputs
    input_file = input("Enter Input File Path (default: data/input data.xlsx): ").strip()
    if not input_file:
        input_file = os.path.join("data", "input data.xlsx")
    
    # 2. Load Data
    print(f"\n[1/4] Loading Data from {input_file}...")
    try:
        loader = DataLoader(input_file)
        original_df, processed_df = loader.load()
        print(f"      Success! Loaded {len(processed_df)} students.")
    except Exception as e:
        print(f"      Error: {e}")
        return

    # 3. Capacity Mode
    print("\n[2/4] Configure Capacities")
    print("      1. Auto-Equalization (Divide students among departments)")
    print("      2. Manual Configuration (Load from 'Settings' sheet)")
    
    mode_input = input("      Select Mode [1/2]: ").strip()
    mode = 'MANUAL' if mode_input == '2' else 'AUTO'
    
    manual_settings = None
    if mode == 'MANUAL':
        manual_settings = loader.get_settings()
        if not manual_settings:
            print("      WARNING: No 'Settings' sheet found. Falling back to AUTO.")
            mode = 'AUTO'
        else:
            print(f"      Loaded Settings for {len(manual_settings)} departments.")

    # 4. Distribute
    print(f"\n[3/4] Running Distribution Algorithm (Mode: {mode})...")
    distributor = Distributor(processed_df)
    distributor.calculate_capacities(mode, manual_settings)
    
    # Print Capacities
    print("      Capacities Plan:")
    for d, c in distributor.capacities.items():
        print(f"      - {d}: {c}")

    results = distributor.distribute()
    
    # Calculate Stats
    assigned_count = len([v for v in results.values() if v])
    total_count = len(processed_df)
    print(f"      Distribution Complete: {assigned_count}/{total_count} students assigned.")

    # 5. Export
    print("\n[4/4] Exporting Results...")
    try:
        out_path = Exporter.export(original_df, results)
        print(f"      Success! Results saved to '{out_path}'")
    except Exception as e:
        print(f"      Error exporting: {e}")

    print("\n" + "="*60)
    print("Done.")

if __name__ == "__main__":
    main()
