#!/usr/bin/env python3
"""
FMU Builder - Dynamic YAML-based build system
Reads project.yaml and generates FMU automatically
"""
import os
import sys
import subprocess
import yaml
from pathlib import Path

# Configuration
IMAGE_NAME = "fmu-builder"
CONTAINER_NAME = "temp-fmu-builder"
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
BUILD_DIR = PROJECT_ROOT / "build"
CONFIG_FILE = PROJECT_ROOT / "project.yaml"

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
            lib_path = INPUT_DIR / lib['path']
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
    script += "// DO NOT EDIT MANUALLY - Edit project.yaml instead\n\n"
    
    # Load external libraries first
    for lib in ext_libs:
        lib_path = f"/input/{lib['path']}"
        script += f'// Load external library: {lib["name"]}\n'
        script += f'loadFile("{lib_path}");\n'
        script += 'getErrorString();\n\n'
    
    # Load main file
    script += f"// Load main model file\n"
    script += f'loadFile("{main_file}");\n'
    script += "getErrorString();\n\n"
    
    # Load dependencies
    for dep in dependencies:
        script += f'loadFile("{dep}");\n'
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
    script += f'    platforms={{"{fmu_config.get("platform", "static")}"}}'
    
    # Add solver if specified
    if 'solver' in fmu_config:
        script += f',\n    solver="{fmu_config["solver"]}"'
    
    script += "\n);\n\n"
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
    
    # 4. Build Docker Image (compiles FMU)
    print("\n[4/5] Building Docker image (compiling FMU)...")
    # Copy generated script to replace build.mos
    build_mos = BUILD_DIR / "build.mos"
    subprocess.run(f'copy "{script_path}" "{build_mos}"', shell=True, check=True)
    
    run_command(f"docker build -f build/Dockerfile -t {IMAGE_NAME} .", cwd=PROJECT_ROOT)
    
    # 5. Extract FMU
    print("\n[5/5] Extracting FMU from image...")
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
    print(f"\nTo test: python tests/test_fmu.py")

if __name__ == "__main__":
    main()
