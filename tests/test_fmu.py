"""
Simple test script to verify the generated FMU works correctly.
This runs a basic simulation and prints the results.
"""
import sys
import os

# Add parent directory to path to import fmpy
try:
    from fmpy import simulate_fmu
    from fmpy.util import plot_result
    import numpy as np
except ImportError:
    print("Error: fmpy not installed. Install with: pip install fmpy")
    sys.exit(1)

# Path to the FMU
fmu_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'DigitalTwin.fmu')

if not os.path.exists(fmu_path):
    print(f"Error: FMU not found at {fmu_path}")
    sys.exit(1)

print("=" * 60)
print("Testing DigitalTwin FMU")
print("=" * 60)

try:
    # Run a simple simulation (10 seconds)
    print("\nRunning simulation...")
    result = simulate_fmu(
        fmu_path,
        stop_time=10.0,
        output_interval=1.0,
        fmi_type='CoSimulation'
    )
    
    print("✅ Simulation completed successfully!")
    
    # Display some key outputs
    print("\n" + "=" * 60)
    print("Sample Results (first 5 time points):")
    print("=" * 60)
    
    # Convert result to a more readable format
    import pandas as pd
    df = pd.DataFrame(result)
    
    # Show key columns
    key_cols = ['time']
    if 'out_MW_gross' in df.columns:
        key_cols.append('out_MW_gross')
    if 'out_FurnaceTemp' in df.columns:
        key_cols.append('out_FurnaceTemp')
    if 'out_Efficiency' in df.columns:
        key_cols.append('out_Efficiency')
    if 'out_NOx' in df.columns:
        key_cols.append('out_NOx')
    
    print(df[key_cols].head())
    
    print("\n" + "=" * 60)
    print("FMU Validation: PASS ✅")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Simulation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
