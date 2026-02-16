import os
import sys
import yaml
import csv
import shutil
import math
import argparse
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave

# Configuration defaults
DEFAULT_STEP_SIZE = 0.1
DEFAULT_TOLERANCE = 0.5

def load_config(config_path="project.yaml"):
    """Load project configuration"""
    if not os.path.exists(config_path):
        print(f"Error: Configuration file {config_path} not found.")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_csv_data(csv_path):
    """Load CSV data into a list of dictionaries"""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found.")
        sys.exit(1)
        
    data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert values to float
            converted_row = {}
            for k, v in row.items():
                try:
                    converted_row[k] = float(v)
                except ValueError:
                    converted_row[k] = v # Keep as string if not float
            data.append(converted_row)
    return data

def run_simulation(fmu_path, config, data):
    """Run FMU simulation and validate against data"""
    
    validation_cfg = config.get('validation', {})
    interface_cfg = config.get('interface', {})
    
    step_size = validation_cfg.get('step_size', DEFAULT_STEP_SIZE)
    global_tolerance = validation_cfg.get('tolerance', DEFAULT_TOLERANCE)
    start_time = validation_cfg.get('start_time', 0.0)
    
    errors = [] # Bug Fix: Initialize error list
    
    # Map CSV headers to FMU variables
    inputs_map = {item['name']: item.get('fmu_variable', item['name']) for item in interface_cfg.get('inputs', [])}
    outputs_map = {item['name']: item.get('fmu_variable', item['name']) for item in interface_cfg.get('outputs', [])}
    output_tolerances = {item['name']: item.get('tolerance', global_tolerance) for item in interface_cfg.get('outputs', [])}

    # Prepare FMU
    model_description = read_model_description(fmu_path)
    
    # Extract FMU
    unzipdir = extract(fmu_path)
    
    fmu = FMU2Slave(guid=model_description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=model_description.coSimulation.modelIdentifier,
                    instanceName='instance1')
    
    fmu.instantiate()
    fmu.setupExperiment(startTime=start_time)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()
    
    current_time = start_time
    
    current_time = start_time
    
    # Sort data by time just in case
    # Try to find time column
    time_col = None
    if data and 'Time' in data[0]:
        time_col = 'Time'
    elif data and 'time' in data[0]:
        time_col = 'time'
    
    if time_col:
        # Sort by time value (float)
        data.sort(key=lambda x: float(x[time_col]))
        print(f"  Synced with CSV column '{time_col}'")
    else:
        print(f"  Warning: No 'Time' column found in CSV. Using fixed step_size={step_size} sequentially.")

    for i, row in enumerate(data):
        # Determine target time
        if time_col:
            target_time = float(row[time_col])
        else:
            target_time = current_time + step_size
            
        # Set Inputs
        for csv_header, fmu_var in inputs_map.items():
            if csv_header in row:
                # Find variable reference
                val_ref = next(v.valueReference for v in model_description.modelVariables if v.name == fmu_var)
                fmu.setReal([val_ref], [float(row[csv_header])])
        
        # Advance Simulation to Target Time
        # Only advance if target is in future.
        if target_time > current_time:
            while current_time < target_time:
                # Calculate next step (don't overshoot)
                remaining = target_time - current_time
                next_step = min(step_size, remaining)
                
                # Guard against tiny steps (float noise)
                if next_step < 1e-6:
                    current_time = target_time
                    break
                
                fmu.doStep(currentCommunicationPoint=current_time, communicationStepSize=next_step)
                current_time += next_step
        
        # Check Outputs (at target_time)
        for csv_header, fmu_var in outputs_map.items():
            if csv_header in row:
                # Get simulation result
                val_ref = next(v.valueReference for v in model_description.modelVariables if v.name == fmu_var)
                sim_val = fmu.getReal([val_ref])[0]
                ref_val = float(row[csv_header])
                
                # Check tolerance
                tol = output_tolerances.get(csv_header, global_tolerance)
                diff = abs(sim_val - ref_val)
                
                if diff > tol:
                    error_msg = f"Time {current_time:.2f}: {csv_header} (FMU: {fmu_var}) mismatch. Sim: {sim_val:.4f}, Ref: {ref_val:.4f}, Diff: {diff:.4f} > Tol: {tol}"
                    print(f"  [FAIL] {error_msg}")
                    errors.append(error_msg)
        
        # Check Outputs
        for csv_header, fmu_var in outputs_map.items():
            if csv_header in row:
                # Get simulation result
                val_ref = next(v.valueReference for v in model_description.modelVariables if v.name == fmu_var)
                sim_val = fmu.getReal([val_ref])[0]
                ref_val = float(row[csv_header])
                
                # Check tolerance
                tol = output_tolerances.get(csv_header, global_tolerance)
                diff = abs(sim_val - ref_val)
                
                if diff > tol:
                    error_msg = f"Time {current_time:.2f}: {csv_header} (FMU: {fmu_var}) mismatch. Sim: {sim_val:.4f}, Ref: {ref_val:.4f}, Diff: {diff:.4f} > Tol: {tol}"
                    print(f"  [FAIL] {error_msg}")
                    errors.append(error_msg)

    fmu.terminate()
    fmu.freeInstance()
    shutil.rmtree(unzipdir)
    
    if errors:
        print(f"\nValidation FAILED with {len(errors)} errors.")
        sys.exit(1)
    else:
        print("\nValidation PASSED! All outputs within tolerance.")

def main():
    parser = argparse.ArgumentParser(description="Generic FMU Validator")
    parser.add_argument("--config", default="project.yaml", help="Path to project.yaml")
    args = parser.parse_args()

    print("Loading configuration...")
    config = load_config(args.config)
    
    if not config.get('validation', {}).get('active', False):
        print("Validation skipped (active: false in project.yaml)")
        sys.exit(0)

    # Locate FMU
    fmu_name = config['fmu'].get('output_name', 'DigitalTwin') + ".fmu"
    # In Docker, FMU is likely in current dir or built to a specific location.
    # The build script puts it in current dir or specific output.
    # Let's assume current directory or search for it.
    fmu_path = fmu_name
    if not os.path.exists(fmu_path):
        # Try finding any .fmu if specific name not found (fallback)
        fmus = [f for f in os.listdir('.') if f.endswith('.fmu')]
        if fmus:
            fmu_path = fmus[0]
        else:
            print(f"Error: FMU {fmu_name} not found in current directory.")
            sys.exit(1)

    print(f"Found FMU: {fmu_path}")

    csv_path = config['validation'].get('csv_file', 'test_data/validation.csv')
    print(f"Loading test data from: {csv_path}")
    data = load_csv_data(csv_path)
    
    run_simulation(fmu_path, config, data)

if __name__ == "__main__":
    main()
