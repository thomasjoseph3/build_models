#!/usr/bin/env python3
"""
Validation CSV Splitter
Splits client-provided validation CSV into test_inputs.csv and expected_outputs.csv
based on interface specs in project.yaml
"""
import csv
import yaml
from pathlib import Path
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
CONFIG_FILE = PROJECT_ROOT / "input" / "project.yaml"
TEST_DATA_DIR = PROJECT_ROOT / "input" / "test_data"

def load_config():
    """Load project configuration"""
    if not CONFIG_FILE.exists():
        print(f"Error: {CONFIG_FILE} not found!")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def split_validation_csv(validation_file, config):
    """
    Split combined validation CSV into inputs and outputs
    
    Expected format of validation CSV:
    time,input1,input2,...,output1,output2,...
    0,10,20,...,100,200,...
    60,15,25,...,150,250,...
    """
    
    validation_path = TEST_DATA_DIR / validation_file
    
    if not validation_path.exists():
        print(f"Error: {validation_path} not found!")
        print(f"Place client validation CSV in: {TEST_DATA_DIR}/")
        sys.exit(1)
    
    # Get input and output names from config
    input_names = [inp['name'] for inp in config['interface']['inputs']]
    output_names = [out['name'] for out in config['interface']['outputs']]
    
    print(f"Reading: {validation_path.name}")
    print(f"Expected inputs ({len(input_names)}): {', '.join(input_names[:3])}...")
    print(f"Expected outputs ({len(output_names)}): {', '.join(output_names[:3])}...")
    
    # Read validation CSV
    with open(validation_path, 'r') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        csv_columns = reader.fieldnames
    
    if not all_rows:
        print("Error: Validation CSV is empty!")
        sys.exit(1)
    
    print(f"\nFound {len(all_rows)} test scenarios")
    print(f"CSV columns: {len(csv_columns)}")
    
    # Validate that expected columns exist
    missing_inputs = [name for name in input_names if name not in csv_columns]
    missing_outputs = [name for name in output_names if name not in csv_columns]
    
    if missing_inputs:
        print(f"\nWarning: Missing input columns: {missing_inputs}")
    if missing_outputs:
        print(f"\nWarning: Missing output columns: {missing_outputs}")
    
    # Split into input and output CSVs
    input_csv_path = TEST_DATA_DIR / "test_inputs.csv"
    output_csv_path = TEST_DATA_DIR / "expected_outputs.csv"
    
    # Write test_inputs.csv
    input_cols = ['time'] + [name for name in input_names if name in csv_columns]
    with open(input_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=input_cols)
        writer.writeheader()
        for row in all_rows:
            input_row = {col: row.get(col, '') for col in input_cols}
            writer.writerow(input_row)
    
    # Write expected_outputs.csv
    output_cols = ['time'] + [name for name in output_names if name in csv_columns]
    with open(output_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_cols)
        writer.writeheader()
        for row in all_rows:
            output_row = {col: row.get(col, '') for col in output_cols}
            writer.writerow(output_row)
    
    print(f"\nSplit complete!")
    print(f"  Created: {input_csv_path.name} ({len(input_cols)} columns)")
    print(f"  Created: {output_csv_path.name} ({len(output_cols)} columns)")
    print(f"\nReady for validation testing!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_validation_csv.py <validation_file.csv>")
        print("\nExample: python split_validation_csv.py client_validation_data.csv")
        print("\nPlace the client CSV in input/test_data/ first")
        sys.exit(1)
    
    validation_file = sys.argv[1]
    config = load_config()
    split_validation_csv(validation_file, config)
