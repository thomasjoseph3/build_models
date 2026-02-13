#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore")

import csv
import sys
import os
import shutil
import yaml
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave

# --- CONFIGURATION (Paths) ---
YAML_PATH = 'project.yaml'
FMU_PATH  = 'ShellAndTubeNTU.fmu'
CSV_PATH  = 'test_data/validation.csv'
TOLERANCE = 0.5
# -----------------------------

def load_config(yaml_file):
    if not os.path.exists(yaml_file):
        print(f"Error: YAML file not found at {yaml_file}")
        sys.exit(1)
    with open(yaml_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Auto-fetch inputs and outputs from YAML schema
    inputs = [v['name'] for v in config['interface']['inputs']]
    outputs = [v['name'] for v in config['interface']['outputs']]
    return inputs, outputs

import faulthandler
faulthandler.enable()

# ...

def main():
    print(f"--- Validation Script (Robust Mode) ---")
    print(f"Config: YAML='{YAML_PATH}', FMU='{FMU_PATH}', CSV='{CSV_PATH}'")
    
    # 1. Parse YAML to identify variables
    inputs, outputs = load_config(YAML_PATH)

    # 2. Verify Files Exist
    if not os.path.exists(FMU_PATH):
        print(f"Error: FMU needed at: {FMU_PATH}")
        sys.exit(1)
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV needed at: {CSV_PATH}")
        sys.exit(1)

    # 3. Load CSV Data
    data = []
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({k: float(v) for k, v in row.items()})
    
    # 4. Prepare FMU Extraction (Extract once to tmp)
    model_description = read_model_description(FMU_PATH)
    unzipdir = extract(FMU_PATH)
    
    # Identify Variable References ONCE
    try:
        input_refs = [next(v.valueReference for v in model_description.modelVariables if v.name == n) for n in inputs]
        output_refs = [next(v.valueReference for v in model_description.modelVariables if v.name == n) for n in outputs]
        # Optional k_factor
        k_ref = next((v.valueReference for v in model_description.modelVariables if v.name == 'k_factor'), None)
    except StopIteration:
        print("Error: Could not find one of the YAML inputs/outputs in the FMU variables.")
        shutil.rmtree(unzipdir, ignore_errors=True)
        sys.exit(1)

    failures = 0
    
    try:
        # 5. Run Validation Loop (Isolated Inputs)
        for i, row in enumerate(data):
            target_time = row.get('Time', 1.0)
            if target_time == 0: target_time = 1.0
            
            print(f"Test Case {i+1}: Simulating {inputs} -> {target_time}s...", flush=True)
            
            # Instantiate per row for isolation
            fmu = FMU2Slave(guid=model_description.guid,
                            unzipDirectory=unzipdir,
                            modelIdentifier=model_description.coSimulation.modelIdentifier,
                            instanceName=f'validator_{i}')
            
            fmu.instantiate()
            fmu.setupExperiment(startTime=0.0)
            
            # Set k_factor (Parameter)
            if k_ref is not None and 'k_factor' in row:
                fmu.setReal([k_ref], [row['k_factor']])
            
            fmu.enterInitializationMode()
            fmu.exitInitializationMode()
            
            # Set Inputs (Constant for this run)
            vals = [row[n] for n in inputs]
            fmu.setReal(input_refs, vals)
            
            # Simulate
            current_time = 0.0
            step_size = 0.01  # Reduced step size (0.01s) triggers CVODE stability
            
            # print(f"  [DEBUG] Starting Loop: 0 -> {target_time}")
            
            while current_time < target_time - 1e-5:
                status = fmu.doStep(currentCommunicationPoint=current_time, communicationStepSize=step_size)
                # fmpy .doStep may return None on success in some versions, or 0 (FMI2_OK)
                if status is not None and status != 0:
                     print(f"  Warning: fmu.doStep returned status {status} at t={current_time}")
                current_time += step_size
            
            # Check Outputs
            res = fmu.getReal(output_refs)
            
            row_failed = False
            for name, val, ref_val in zip(outputs, res, [row[n] for n in outputs]):
                diff = abs(val - ref_val)
                # Use relative tolerance for large values? Or fixed?
                # User config has tolerance_percent=5.0. 
                # Script hardcoded TOLERANCE = 0.5.
                # I'll use 0.5 as requested by user script.
                if diff > TOLERANCE:
                    print(f"  FAIL: {name} FMU={val:.2f} CSV={ref_val:.2f} (Diff={diff:.2f})")
                    row_failed = True
            
            if row_failed:
                failures += 1
            else:
                print("  PASS")
            
            fmu.terminate()
            fmu.freeInstance()

    finally:
        shutil.rmtree(unzipdir, ignore_errors=True)
    
    if failures == 0:
        print(f"SUCCESS: All {len(data)} tests passed.")
    else:
        print(f"FAILURE: {failures}/{len(data)} tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
