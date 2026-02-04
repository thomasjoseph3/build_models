"""
Biomass Boiler FMU Simulation Script
5-Hour Normal Operation with Level-Weighted NOx
"""
import fmpy
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import shutil
import csv
import os

fmu_path = 'DigitalTwin.fmu'

def run_simulation():
    print(f"--- Loading FMU: {fmu_path} ---")
    if not os.path.exists(fmu_path):
        print("ERROR: FMU file not found!")
        return

    description = read_model_description(fmu_path)
    vrs = {var.name: var.valueReference for var in description.modelVariables}
    print(f"Found {len(vrs)} variables in FMU")
    
    unzipdir = extract(fmu_path)
    fmu = FMU2Slave(guid=description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=description.coSimulation.modelIdentifier,
                    instanceName='boiler1')
    
    fmu.instantiate()
    fmu.setupExperiment(startTime=0.0)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()
    
    # =========================================
    # SIMULATION PARAMETERS: 5 Hours
    # =========================================
    step_size = 10.0        # 10 second steps
    final_time = 18000.0    # 5 hours = 18000 seconds
    output_interval = 300.0 # Output every 5 minutes (300s)
    
    print(f"--- 5-Hour Simulation: {final_time/3600:.1f} hours ---")
    print(f"    Step size: {step_size}s, Output every: {output_interval}s")
    
    # =========================================
    # NORMAL OPERATION SCENARIO
    # Realistic 5-hour shift with gradual changes
    # =========================================
    # Hour 0-1: Startup/warmup with 3 mills
    # Hour 1-3: Steady operation at 4 mills (80% load)
    # Hour 3-4: Ramp up to 5 mills (100% load)
    # Hour 4-5: Steady 5 mills operation
    
    base_inputs = {
        'feeder1_flow': 5.0, 'feeder2_flow': 5.0, 'feeder3_flow': 5.0,
        'feeder4_flow': 0.0, 'feeder5_flow': 0.0,
        'fuel_moisture': 40.0, 'fuel_LHV': 17.5,
        'primaryAir_flow': 55.0, 'primaryAir_temp': 25.0,
        'secondaryAir_flow': 45.0, 'overfireAir_flow': 10.0,
        'fgr_percent': 8.0, 'target_MW': 80.0
    }
    current_inputs = base_inputs.copy()
    
    # Output mapping
    output_map = {
        'boiler.efficiencyPercent': 'out_Efficiency',
        'boiler.furnacePressurePa': 'out_Draft',
        'furnace.exitGasTemperatureC': 'out_FurnaceTemp',
        'furnace.o2Percent': 'out_O2',
        'flueGas.o2Percent': 'out_O2',
        'flueGas.coPpm': 'out_CO',
        'flueGas.noxMgPerNm3': 'out_NOx',
        'steam.massFlowRateKgPerS': 'out_steam_flow',
        'turbine.powerOutputMW': 'out_MW_gross',
        'mill1.motorPowerKw': 'mill1_power', 'mill1.outletTemperatureC': 'mill1_temp',
        'mill2.motorPowerKw': 'mill2_power', 'mill2.outletTemperatureC': 'mill2_temp',
        'mill3.motorPowerKw': 'mill3_power', 'mill3.outletTemperatureC': 'mill3_temp',
        'mill4.motorPowerKw': 'mill4_power', 'mill4.outletTemperatureC': 'mill4_temp',
        'mill5.motorPowerKw': 'mill5_power', 'mill5.outletTemperatureC': 'mill5_temp',
        # NEW DYNAMIC OUTPUTS
        'steam.pressureBar': 'out_SteamPressure',
        'steam.temperatureC': 'out_SteamTemperature',
        'flueGas.temperatureC': 'out_FlueGasTemp',
        'feedwater.flowRateKgPerS': 'out_FeedwaterFlow',
        'feedwater.temperatureC': 'out_FeedwaterTemp',
        'primaryAir.fanSpeedRpm': 'out_PAFanRPM',
        'idFan.speedRpm': 'out_IDFanRPM',
        'levelPairCode': 'out_LevelPair',
    }
    
    # Note: active_mill_count and nox_level_weight are internal variables, 
    # not in CURRENT_SCHEMA, so we don't include them in CSV output
    
    rows = []
    time = 0.0
    next_output = 0.0
    
    print("\n=== SCENARIO ===")
    print("  Hour 0-1:   Warmup - 3 mills (15 kg/s fuel)")
    print("  Hour 1-3:   Steady - 4 mills (20 kg/s fuel)")
    print("  Hour 3-4:   Ramp up - 5 mills (25 kg/s fuel)")
    print("  Hour 4-5:   Full load - 5 mills steady")
    print("")
    
    while time <= final_time:
        hour = time / 3600.0
        
        # =========================================
        # SCENARIO LOGIC (Gradual Load Changes)
        # =========================================
        if hour < 1.0:
            # Hour 0-1: Warmup with 3 mills (L1, L2, L3)
            current_inputs['feeder1_flow'] = 5.0
            current_inputs['feeder2_flow'] = 5.0
            current_inputs['feeder3_flow'] = 5.0
            current_inputs['feeder4_flow'] = 0.0
            current_inputs['feeder5_flow'] = 0.0
            current_inputs['primaryAir_flow'] = 55.0
            current_inputs['secondaryAir_flow'] = 45.0
        elif hour < 3.0:
            # Hour 1-3: Add mill 4 (L1, L2, L3, L4)
            current_inputs['feeder4_flow'] = 5.0
            current_inputs['feeder5_flow'] = 0.0
            current_inputs['primaryAir_flow'] = 68.0
            current_inputs['secondaryAir_flow'] = 55.0
        elif hour < 4.0:
            # Hour 3-4: Add mill 5 (all 5 mills, L1-L5)
            current_inputs['feeder5_flow'] = 5.0
            current_inputs['primaryAir_flow'] = 75.0
            current_inputs['secondaryAir_flow'] = 58.0
        else:
            # Hour 4-5: Steady at full load
            pass  # Keep previous settings
        
        # Apply inputs
        for name, val in current_inputs.items():
            if name in vrs:
                fmu.setReal([vrs[name]], [val])
        
        fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
        time += step_size
        
        if time >= next_output:
            row = {'timestamp': f'{hour:.2f}h'}
            
            # Collect outputs
            for schema_key, fmu_var in output_map.items():
                if fmu_var in vrs:
                    row[schema_key] = round(fmu.getReal([vrs[fmu_var]])[0], 2)
            
            # Echo inputs
            total_fuel = sum([current_inputs[f'feeder{i}_flow'] for i in range(1,6)])
            total_air = current_inputs['primaryAir_flow'] + current_inputs['secondaryAir_flow'] + current_inputs['overfireAir_flow']
            
            row['feeder1.flowRateKgPerS'] = current_inputs['feeder1_flow']
            row['feeder2.flowRateKgPerS'] = current_inputs['feeder2_flow']
            row['feeder3.flowRateKgPerS'] = current_inputs['feeder3_flow']
            row['feeder4.flowRateKgPerS'] = current_inputs['feeder4_flow']
            row['feeder5.flowRateKgPerS'] = current_inputs['feeder5_flow']
            row['fuel.moisturePercent'] = current_inputs['fuel_moisture']
            row['fuel.lowerHeatingValueMJPerKg'] = current_inputs['fuel_LHV']
            row['primaryAir.flowRateKgPerS'] = current_inputs['primaryAir_flow']
            row['primaryAir.temperatureC'] = current_inputs['primaryAir_temp']
            row['secondaryAir.flowRateKgPerS'] = current_inputs['secondaryAir_flow']
            row['overfireAir.flowRateKgPerS'] = current_inputs['overfireAir_flow']
            row['fgr.recirculationPercent'] = current_inputs['fgr_percent']
            row['plant.targetSteamMW'] = current_inputs['target_MW']
            row['totalFuel_kgPerS'] = total_fuel
            row['totalAir_kgPerS'] = total_air
            
            for i in range(1, 6):
                row[f'mill{i}.status'] = 'running' if current_inputs[f'feeder{i}_flow'] > 0.1 else 'stopped'
            
            rows.append(row)
            next_output += output_interval
            
            # Progress indicator
            if len(rows) % 12 == 0:  # Every hour
                print(f"  Simulated: {hour:.1f} hours...")
    
    fmu.terminate()
    fmu.freeInstance()
    shutil.rmtree(unzipdir)
    
    # Write CSV
    csv_file = 'simulation_results_5hr.csv'
    if rows:
        fieldnames = ['timestamp', 'totalFuel_kgPerS', 'totalAir_kgPerS'] + sorted([k for k in rows[0].keys() if k not in ['timestamp', 'totalFuel_kgPerS', 'totalAir_kgPerS']])
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"\n--- CSV Generated: {csv_file} ({len(rows)} rows) ---\n")
        
        # Summary table - show key transition points
        print("=== KEY METRICS SUMMARY (Selected Points) ===")
        print(f"{'Time':<10} {'Mills':<6} {'Fuel':<8} {'Air':<8} {'Temp°C':<10} {'O2%':<8} {'MW':<8} {'Eff%':<8} {'NOx':<10} {'CO':<8}")
        print("-" * 95)
        
        # Show specific rows: start, each phase change, end
        key_indices = [0, 11, 12, 35, 36, 47, 48, 59]  # Approximately at phase changes
        for i, idx in enumerate(key_indices):
            if idx < len(rows):
                r = rows[idx]
                mills = sum([1 for j in range(1,6) if r[f'mill{j}.status'] == 'running'])
                print(f"{r['timestamp']:<10} {mills:<6} {r['totalFuel_kgPerS']:<8} {r['totalAir_kgPerS']:<8} {r.get('furnace.exitGasTemperatureC','N/A'):<10} {r.get('furnace.o2Percent','N/A'):<8} {r.get('turbine.powerOutputMW','N/A'):<8} {r.get('boiler.efficiencyPercent','N/A'):<8} {r.get('flueGas.noxMgPerNm3','N/A'):<10} {r.get('flueGas.coPpm','N/A'):<8}")
        
        # Show last row
        r = rows[-1]
        mills = sum([1 for j in range(1,6) if r[f'mill{j}.status'] == 'running'])
        print(f"{r['timestamp']:<10} {mills:<6} {r['totalFuel_kgPerS']:<8} {r['totalAir_kgPerS']:<8} {r.get('furnace.exitGasTemperatureC','N/A'):<10} {r.get('furnace.o2Percent','N/A'):<8} {r.get('turbine.powerOutputMW','N/A'):<8} {r.get('boiler.efficiencyPercent','N/A'):<8} {r.get('flueGas.noxMgPerNm3','N/A'):<10} {r.get('flueGas.coPpm','N/A'):<8}")

if __name__ == "__main__":
    run_simulation()
