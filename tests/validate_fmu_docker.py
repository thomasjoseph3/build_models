#!/usr/bin/env python3
"""
FMU Validation Script - Docker Version
Runs inside the Docker container during build
Validates FMU with test data and exits with error if validation fails
"""
import os
import sys
import csv
import yaml
from pathlib import Path
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import shutil

# Paths (inside Docker container)
WORK_DIR = Path("/build")
CONFIG_FILE = WORK_DIR / "project.yaml"
TEST_DATA_DIR = WORK_DIR / "test_data"

def load_config():
    """Load project configuration"""
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def find_fmu():
    """Find the FMU file in current directory"""
    fmu_files = list(WORK_DIR.glob("*.fmu"))
    if not fmu_files:
        print("ERROR: No FMU found in /build directory!")
        sys.exit(1)
    return fmu_files[0]

def load_csv(filepath):
    """Load CSV file into list of dicts"""
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def validate_fmu(config, fmu_path):
    """Run FMU with test inputs and compare with expected outputs"""
    
    input_csv = TEST_DATA_DIR / "test_inputs.csv"
    expected_csv = TEST_DATA_DIR / "expected_outputs.csv"
    
    if not input_csv.exists():
        print("No test_inputs.csv - skipping validation")
        return True
    
    print(f"\n{'='*60}")
    print("FMU VALIDATION TEST (Docker)")
    print(f"{'='*60}\n")
    
    # Load FMU
    print(f"Loading FMU: {fmu_path.name}")
    description = read_model_description(fmu_path)
    vrs = {var.name: var.valueReference for var in description.modelVariables}
    
    unzipdir = extract(fmu_path)
    fmu = FMU2Slave(
        guid=description.guid,
        unzipDirectory=unzipdir,
        modelIdentifier=description.coSimulation.modelIdentifier,
        instanceName='validation_test'
    )
    
    fmu.instantiate()
    fmu.setupExperiment(startTime=0.0)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()
    
    # Load test data
    test_inputs = load_csv(input_csv)
    expected_outputs = load_csv(expected_csv) if expected_csv.exists() else []
    
    # Get tolerance from config
    tolerance_pct = config.get('validation', {}).get('tolerance_percent', 5.0)
    
    # Get I/O mapping from config
    input_map = {inp['name']: inp for inp in config['interface']['inputs']}
    output_map = {out['name']: out for out in config['interface']['outputs']}
    
    print(f"Test scenarios: {len(test_inputs)}")
    print(f"Tolerance: ±{tolerance_pct}%\n")
    
    # Run simulation
    failures = []
    
    for i, test_row in enumerate(test_inputs):
        time = float(test_row['time'])
        
        # Set inputs
        for input_name, input_spec in input_map.items():
            if input_name in test_row:
                value = float(test_row[input_name])
                if input_name in vrs:
                    fmu.setReal([vrs[input_name]], [value])
        
        # Step simulation
        fmu.doStep(currentCommunicationPoint=time, communicationStepSize=1.0)
        
        # Read outputs
        actual_outputs = {}
        for output_name, output_spec in output_map.items():
            fmu_var = output_spec.get('fmu_variable', output_name)
            if fmu_var in vrs:
                actual_outputs[output_name] = fmu.getReal([vrs[fmu_var]])[0]
        
        # Compare with expected
        if i < len(expected_outputs):
            expected_row = expected_outputs[i]
            print(f"[{i+1}/{len(test_inputs)}] Time={time}s")
            
            for output_name in actual_outputs:
                actual = actual_outputs[output_name]
                
                if output_name in expected_row:
                    expected = float(expected_row[output_name])
                    
                    # Calculate error
                    if expected != 0:
                        error_pct = abs((actual - expected) / expected) * 100
                    else:
                        error_pct = 0 if abs(actual) < 1e-6 else 100
                    
                    # Check tolerance
                    status = "PASS" if error_pct <= tolerance_pct else "FAIL"
                    
                    print(f"  {status} {output_name}: {actual:.2f} (expected: {expected:.2f}, error: {error_pct:.1f}%)")
                    
                    if error_pct > tolerance_pct:
                        failures.append({
                            'time': time,
                            'output': output_name,
                            'actual': actual,
                            'expected': expected,
                            'error_pct': error_pct
                        })
    
    fmu.terminate()
    fmu.freeInstance()
    shutil.rmtree(unzipdir)
    
    # Summary
    print(f"\n{'='*60}")
    if expected_outputs:
        if failures:
            print(f"VALIDATION FAILED")
            print(f"Failures: {len(failures)}/{len(expected_outputs)}")
            print(f"\nFailed checks:")
            for fail in failures[:10]:
                print(f"  - Time {fail['time']}s: {fail['output']} = {fail['actual']:.2f} (expected {fail['expected']:.2f}, {fail['error_pct']:.1f}% error)")
            print(f"{'='*60}\n")
            return False
        else:
            print(f"VALIDATION PASSED")
            print(f"All {len(expected_outputs)} test cases within ±{tolerance_pct}% tolerance")
            print(f"{'='*60}\n")
            return True
    else:
        print("SIMULATION COMPLETED")
        print("(No expected outputs provided for validation)")
        print(f"{'='*60}\n")
        return True

if __name__ == "__main__":
    try:
        config = load_config()
        fmu_path = find_fmu()
        passed = validate_fmu(config, fmu_path)
        
        if not passed:
            print("ERROR: Validation failed - FMU will not be delivered!")
            sys.exit(1)
        
        print("SUCCESS: FMU validated and ready for delivery!")
        sys.exit(0)
        
    except Exception as e:
        print(f"ERROR during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
