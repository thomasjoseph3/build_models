#!/usr/bin/env python3
"""
FMU Builder - Dynamic YAML-based build system
Reads project.yaml and generates FMU automatically
"""
import os
import sys
import subprocess
import shutil
import yaml
from pathlib import Path

# Configuration
IMAGE_NAME = "fmu-builder"
CONTAINER_NAME = "temp-fmu-builder"
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
INPUT_DIR = PROJECT_ROOT / "input" / "_active"
OUTPUT_DIR = PROJECT_ROOT / "output"
BUILD_DIR = PROJECT_ROOT / "build"
TEST_DATA_DIR = PROJECT_ROOT / "input" / "_active" / "test_data"
CONFIG_FILE = PROJECT_ROOT / "input" / "_active" / "project.yaml"

def log(msg):
    """Print with visual separator"""
    print(f"\n{'='*60}")
    print(msg)
    print('='*60)

def run_command(cmd, cwd=None):
    """Execute shell command and exit on failure"""
    print(f"\nRunning: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error executing command: {cmd}")
        sys.exit(1)

def load_config():
    """Load and validate project.yaml"""
    if not CONFIG_FILE.exists():
        print(f"Error: {CONFIG_FILE} not found!")
        print(f"Create one using project.yaml.example as a template")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required = ['project', 'modelica', 'files', 'fmu']
    for field in required:
        if field not in config:
            print(f"Error: '{field}' section missing in project.yaml")
            sys.exit(1)
    
    if 'model_class' not in config['modelica']:
        print("Error: 'modelica.model_class' is required in project.yaml")
        sys.exit(1)
    
    if 'main' not in config['files']:
        print("Error: 'files.main' is required in project.yaml")
        sys.exit(1)
    
    return config

def validate_files(config):
    """Check that all referenced files exist"""
    src_dir = INPUT_DIR / "src"
    # Support both old flat structure and new model/ structure
    if (src_dir / "model").exists():
        fallback_dir = src_dir / "model"
    else:
        fallback_dir = src_dir
    
    # Check main file
    main_file = src_dir / config['files']['main']
    if not main_file.exists():
        print(f"Error: Main file not found: {main_file}")
        sys.exit(1)
    
    # Check dependencies
    for dep in config['files'].get('dependencies', []):
        dep_file = src_dir / dep
        if not dep_file.exists():
            print(f"Error: Dependency file not found: {dep_file}")
            sys.exit(1)
    
    # Check external libraries
    for lib in config.get('external_libraries', []):
        if 'path' in lib:
            # Libraries are expected to be in src/libraries/
            lib_path = src_dir / "libraries" / lib['path']
            if not lib_path.exists():
                print(f"Error: External library not found: {lib_path}")
                sys.exit(1)
    
    print(f"All files validated")

def generate_build_script(config):
    """Generate build.mos from YAML config"""
    
    model_class = config['modelica']['model_class']
    main_file = config['files']['main']
    dependencies = config['files'].get('dependencies', [])
    ext_libs = config.get('external_libraries', [])
    fmu_config = config['fmu']
    
    # Build the OpenModelica script
    script = "// Auto-generated build script from project.yaml\n"
    # Load MSL if specified
    msl_version = config['modelica'].get('msl_version', 'default')
    if msl_version != 'default':
        script += f'// Load Modelica Standard Library v{msl_version}\n'
        script += f'installPackage(Modelica, "{msl_version}");\n'
        script += "getErrorString();\n\n"
        # Also load Complex if needed (often needed with MSL 4.0)
        if msl_version.startswith("4."):
            script += f'installPackage(Complex, "{msl_version}");\n'
            script += "getErrorString();\n\n"
    
    # Load external libraries first (from input/src/libraries/)
    for lib in ext_libs:
        lib_path = f"input/src/libraries/{lib['path']}"
        script += f'// Load external library: {lib["name"]}\n'
        script += f'loadFile("{lib_path}");\n'
        script += 'getErrorString();\n\n'
    
    # Load main file (from input/src/model/)
    script += f"// Load main model file\n"
    script += f'loadFile("input/src/{main_file}");\n'
    script += "getErrorString();\n\n"
    
    # Load dependencies (from input/src/model/)
    for dep in dependencies:
        script += f'loadFile("input/src/{dep}");\n'
        script += 'getErrorString();\n'
    
    if dependencies:
        script += "\n"
    
    # Build FMU
    script += "// Build FMU\n"
    script += "buildModelFMU(\n"
    script += f"    {model_class},\n"
    script += f'    version="{fmu_config.get("version", "2.0")}",\n'
    script += f'    fmuType="{fmu_config.get("type", "cs")}",\n'
    script += f'    fileNamePrefix="{fmu_config.get("output_name", "DigitalTwin")}",\n'
    script += f'    platforms={{"{fmu_config.get("platform", "static")}"}}\n'
    
    # Note: solver parameter not supported in buildModelFMU
    # OpenModelica uses CVODE by default (recommended)
    # if 'solver' in fmu_config:
    #     script += f',\n    solver="{fmu_config["solver"]}"'
    
    script += ");\n\n"
    script += "// Print any errors\n"
    script += "getErrorString();\n"
    
    # Save generated script
    generated_script = BUILD_DIR / "generated_build.mos"
    with open(generated_script, 'w') as f:
        f.write(script)
    
    print(f"Generated build script: {generated_script}")
    return generated_script

def main():
    log("FMU Builder - YAML-Based Automation")
    
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Config File: {CONFIG_FILE}")
    
    # 1. Load and validate config
    print("\n[1/5] Loading project.yaml...")
    config = load_config()
    print(f"Project: {config['project']['name']}")
    print(f"Model: {config['modelica']['model_class']}")
    
    # 2. Validate files
    print("\n[2/5] Validating files...")
    validate_files(config)
    
    # 3. Generate build script
    print("\n[3/5] Generating OpenModelica script...")
    script_path = generate_build_script(config)
    
    # 4. Build Docker Image (compiles FMU + runs validation)
    print("\n[4/5] Building Docker image (compiling FMU + validation)...")
    
    # Check for client validation CSV and auto-split
    # Check for client validation CSV and auto-split
    validation_config = config.get('validation', {})
    csv_filename = validation_config.get('csv_file', 'validation.csv')
    client_csv = TEST_DATA_DIR / csv_filename
    
    if client_csv.exists():
        print(f"  Found client validation CSV: {client_csv.name}")
        print("  Auto-generating test inputs and expected outputs...")
        
        # Import split function dynamically to avoid circular imports or path issues
        sys.path.append(str(BUILD_DIR))
        from split_validation_csv import split_validation_csv
        try:
            split_validation_csv(client_csv.name, config)
        except Exception as e:
            print(f"  Warning: Failed to split CSV: {e}")
            print("  Validation might fail if test_inputs.csv is missing.")
            
    # Check if test data exists
    has_test_data = (TEST_DATA_DIR / "test_inputs.csv").exists()
    if has_test_data:
        print("  Test data found - validation will run in container")
    else:
        print("  No test data - skipping validation")
    
    # Copy generated script to replace build.mos
    build_mos = BUILD_DIR / "build.mos"
    shutil.copy(str(script_path), str(build_mos))
    
    # Copy validation script to tests folder (Docker will copy it)
    # Docker build will:
    # 1. Compile FMU
    # 2. Install Python + fmpy
    # 3. Run validation (if test data exists)
    # 4. Exit with error if validation fails
    
    # Use call instead of run to stream output directly to stdout
    result_code = subprocess.call(f"docker build --no-cache -f build/Dockerfile -t {IMAGE_NAME} .", 
                          shell=True, cwd=PROJECT_ROOT)
    
    if result_code != 0:
        print("\nERROR: Docker build failed!")
        if has_test_data:
            print("This could be due to:")
            print("  1. OpenModelica compilation error")
            print("  2. FMU validation failed (outputs outside tolerance)")
            print(f"\nCheck Docker build logs above for details.")
        sys.exit(1)
    
    print("\n  Docker build successful!")
    if has_test_data:
        print("  FMU validated inside container - all tests passed!")
    
    # 5. Extract FMU
    print("\n[5/5] Extracting validated FMU from image...")
    subprocess.run(f"docker rm -f {CONTAINER_NAME}", shell=True, stderr=subprocess.DEVNULL)
    
    run_command(f"docker create --name {CONTAINER_NAME} {IMAGE_NAME}")
    
    fmu_name = f"{config['fmu'].get('output_name', 'DigitalTwin')}.fmu"
    dst_fmu = OUTPUT_DIR / fmu_name
    
    if dst_fmu.exists():
        dst_fmu.unlink()
    
    run_command(f'docker cp {CONTAINER_NAME}:/build/{fmu_name} "{dst_fmu}"')
    
    # Cleanup
    subprocess.run(f"docker rm {CONTAINER_NAME}", shell=True, stderr=subprocess.DEVNULL)
    
    log("BUILD SUCCESS")
    print(f"FMU Location: {dst_fmu}")
    print(f"FMU Size: {dst_fmu.stat().st_size / 1024:.1f} KB")
    
    if has_test_data:
        print(f"\nValidation: PASSED (tested inside Docker)")
        print(f"  Tolerance: ±{config.get('validation', {}).get('tolerance_percent', 5.0)}%")
    else:
        print(f"\nNo validation performed (no test data provided)")
    
    print(f"\nFMU is ready for delivery!")

if __name__ == "__main__":
    main()
