import sys
import csv
import yaml
from pathlib import Path
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import shutil

# Paths
WORK_DIR = Path(".")
# Docker runs in /build, so this script is in /build/test_data/test_script.py
# But WORKDIR is /build.
# So if we run `python3 test_data/test_script.py`, valid relative paths depend on CWD.
# Dockerfile WORKDIR is `/build`.
# So paths are relative to `/build`.
CONFIG_FILE = Path("project.yaml")
TEST_DATA_FILE = Path("test_data/validation.csv")
FMU_FILE = list(Path(".").glob("*.fmu"))[0]

def parse_time(val):
    val = val.strip().lower()
    try:
        if val.endswith('h'):
            return float(val[:-1]) * 3600.0
        elif val.endswith('m'):
            return float(val[:-1]) * 60.0
        elif val.endswith('s'):
            return float(val[:-1])
        return float(val)
    except ValueError:
        return 0.0

def run_test():
    print(f"--- Custom Test Script for {FMU_FILE.name} ---", flush=True)
    
    # 1. Load Data
    if not TEST_DATA_FILE.exists():
        print("Error: validation.csv not found")
        sys.exit(1)
        
    with open(TEST_DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"Loaded {len(rows)} test rows from {TEST_DATA_FILE}", flush=True)
    
    # 2. Extract FMU
    description = read_model_description(FMU_FILE)
    unzipdir = extract(FMU_FILE)
    
    fmu = FMU2Slave(
        guid=description.guid,
        unzipDirectory=unzipdir,
        modelIdentifier=description.coSimulation.modelIdentifier,
        instanceName='test'
    )
    
    fmu.instantiate()
    fmu.setupExperiment(startTime=0.0)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()
    
    # 3. Simulate
    vrs = {v.name: v.valueReference for v in description.modelVariables}
    
    # Project specific inputs mapping
    # Validation CSV headers might differ from FMU
    # In "Standard v3.0", developer handles this mapping manually here!
    
    # For BiomassBoiler, headers in validation.csv ARE mapped to inputs in project.yaml?
    # No, remember the "Data Mapping" discussion? The CSV had "feeder1.flowRateKgPerS".
    # The FMU expects "feeder1_flow".
    # I must map them here. 
    
    # Mapping Dict (CSV_Col -> FMU_Input)
    mapping = {
        'feeder1.flowRateKgPerS': 'feeder1_flow',
        'feeder2.flowRateKgPerS': 'feeder2_flow',
        'feeder3.flowRateKgPerS': 'feeder3_flow', 
        'feeder4.flowRateKgPerS': 'feeder4_flow',
        'feeder5.flowRateKgPerS': 'feeder5_flow',
        'primaryAir.flowRateKgPerS': 'primaryAir_flow',
        'primaryAir.temperatureC': 'primaryAir_temp',
        'secondaryAir.flowRateKgPerS': 'secondaryAir_flow',
        'overfireAir.flowRateKgPerS': 'overfireAir_flow',
        'fgr.percent': 'fgr_percent',
        'plant.targetSteamMW': 'target_MW',
        'fuel.moisturePercent': 'fuel_moisture',
        'fuel.lowerHeatingValueMjPerKg': 'fuel_LHV' 
    }

    # CSV Time Column
    # It might be "time" or "timestamp"
    time_col = 'timestamp' # Based on previous knowledge of Biomass CSV
    if 'time' in reader.fieldnames: time_col = 'time'
    if 'Time' in reader.fieldnames: time_col = 'Time'
    
    for i, row in enumerate(rows):
        # Time
        t_str = row.get(time_col, '0')
        time = parse_time(t_str)
        
        # Set Inputs
        for csv_col, fmu_in in mapping.items():
            if csv_col in row:
                val = float(row[csv_col])
                if fmu_in in vrs:
                    fmu.setReal([vrs[fmu_in]], [val])
        
        fmu.doStep(currentCommunicationPoint=time, communicationStepSize=1.0)
        
        # Check Outputs (Optional for now, preventing crash is step 1)
        # ...
        
    print("Simulation completed successfully!", flush=True)
    fmu.terminate()
    fmu.freeInstance()
    shutil.rmtree(unzipdir)

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Test Failed: {e}", flush=True)
        sys.exit(1)
