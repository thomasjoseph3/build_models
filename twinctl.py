#!/usr/bin/env python3
"""
twinctl - The Digital Twin Factory Controller
Unified CLI for building, testing, and managing FMU models.

Usage:
  python3 twinctl.py list                - List available models
  python3 twinctl.py build <model>       - Build a specific model's FMU
  python3 twinctl.py build --all         - Build all models
  python3 twinctl.py validate <model>    - Check model structure
  python3 twinctl.py clean               - Remove artifacts
"""
import argparse
import sys
import subprocess
import shutil
import os
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).resolve().parent
MODELS_DIR = ROOT_DIR / "input" / "models"
ACTIVE_DIR = ROOT_DIR / "input" / "_active"
OUTPUT_DIR = ROOT_DIR / "output"
BUILD_SCRIPT = ROOT_DIR / "build" / "build_fmu.py"

def run_command(cmd, cwd=None):
    """Run a shell command"""
    print(f"[{cmd}]")
    try:
        subprocess.check_call(cmd, shell=True, cwd=cwd)
    except subprocess.CalledProcessError:
        print(f"\nError executing command.")
        sys.exit(1)

def get_available_models():
    """List all model directories under input/models/"""
    if not MODELS_DIR.exists():
        return []
    return sorted([
        d.name for d in MODELS_DIR.iterdir()
        if d.is_dir() and (d / "project.yaml").exists()
    ])

def stage_model(model_name):
    """Copy model files into the _active staging area for building"""
    model_dir = MODELS_DIR / model_name

    if not model_dir.exists():
        print(f"Error: Model '{model_name}' not found in input/models/")
        print(f"Available models: {', '.join(get_available_models()) or 'none'}")
        sys.exit(1)

    if not (model_dir / "project.yaml").exists():
        print(f"Error: project.yaml missing in input/models/{model_name}/")
        sys.exit(1)

    print(f"--- Staging model: {model_name} ---")
    
    # Retry helper
    def retry_rmtree(path, retries=3, delay=1.0):
        import time
        for i in range(retries):
            try:
                shutil.rmtree(path)
                return
            except OSError as e:
                if i == retries - 1:
                    raise e
                print(f"  Warning: Cleanup failed ({e}), retrying in {delay}s...")
                time.sleep(delay)

    # Clean active directory
    if ACTIVE_DIR.exists():
        try:
            retry_rmtree(ACTIVE_DIR)
        except OSError as e:
            print(f"Error: Failed to clean staging directory: {e}")
            print("  Please ensure no files in input/_active/ are open.")
            sys.exit(1)
            
    ACTIVE_DIR.mkdir(parents=True)

    # Copy model files to active
    try:
        if (model_dir / "src").exists():
            shutil.copytree(model_dir / "src", ACTIVE_DIR / "src")
        else:
            print("Warning: No src/ folder in model directory")

        if (model_dir / "test_data").exists():
            shutil.copytree(model_dir / "test_data", ACTIVE_DIR / "test_data")
        else:
            (ACTIVE_DIR / "test_data").mkdir()

        shutil.copy(model_dir / "project.yaml", ACTIVE_DIR / "project.yaml")
        print(f"  Files staged to input/_active/")
    except Exception as e:
        print(f"Error staging model files: {e}")
        sys.exit(1)

def cmd_list(args):
    """List available models"""
    models = get_available_models()
    if not models:
        print("No models found in input/models/")
        print("Create one at: input/models/<name>/")
        return

    print(f"--- Available Models ({len(models)}) ---")
    for model in models:
        model_dir = MODELS_DIR / model
        # Read project name from yaml if possible
        try:
            import yaml
            with open(model_dir / "project.yaml") as f:
                config = yaml.safe_load(f)
            desc = config.get('project', {}).get('description', '')
            print(f"  {model:20s} {desc}")
        except Exception:
            print(f"  {model}")

def cmd_build(args):
    """Build FMU for a model"""
    if args.all:
        # Build all models
        models = get_available_models()
        if not models:
            print("No models found in input/models/")
            sys.exit(1)

        print(f"--- Building all {len(models)} models ---\n")
        results = {}
        for model in models:
            print(f"\n{'='*60}")
            print(f"Building: {model}")
            print(f"{'='*60}")
            
            # 1. Validation First (Fail Fast)
            print("Phase 1: Validation")
            if not validate_single_model(model):
                print(f"  [FAIL] Validation failed for {model}. Skipping build.")
                results[model] = "FAIL (Validation)"
                continue
            
            # 2. Build Process
            print("\nPhase 2: Build")
            try:
                stage_model(model)
                subprocess.check_call(
                    f"{sys.executable} build/build_fmu.py",
                    shell=True, cwd=ROOT_DIR
                )
                # Rename output FMU to model name
                _rename_output_fmu(model)
                results[model] = "PASS"
            except (subprocess.CalledProcessError, SystemExit):
                results[model] = "FAIL (Build)"
                print(f"\nWARNING: Build failed for {model}, continuing...\n")

        # Summary
        print(f"\n{'='*60}")
        print("BUILD SUMMARY")
        print(f"{'='*60}")
        for model, status in results.items():
            icon = "✅" if status == "PASS" else "❌"
            print(f"  {icon} {model}: {status}")
        
        failed = sum(1 for s in results.values() if s.startswith("FAIL"))
        if failed:
            print(f"\n{failed}/{len(models)} builds failed.")
            sys.exit(1)
        print(f"\nAll {len(models)} builds succeeded!")
    else:
        # Build single model
        if not args.model:
            print("Error: Specify a model name or use --all")
            print(f"Available models: {', '.join(get_available_models()) or 'none'}")
            sys.exit(1)

        print(f"--- twinctl: Building {args.model} ---")
        
        # 1. Validation First
        if not validate_single_model(args.model):
            print(f"\n[FAIL] Validation failed for {args.model}. Build aborted.")
            sys.exit(1)

        # 2. Build Process
        print("\n--- Phase 2: Docker Build ---")
        stage_model(args.model)
        run_command(f"{sys.executable} build/build_fmu.py")
        _rename_output_fmu(args.model)

def _rename_output_fmu(model_name):
    """Rename the generic DigitalTwin.fmu to <model_name>.fmu"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read the output name from the active project.yaml
    try:
        import yaml
        with open(ACTIVE_DIR / "project.yaml") as f:
            config = yaml.safe_load(f)
        fmu_name = config.get('fmu', {}).get('output_name', 'DigitalTwin')
    except Exception:
        fmu_name = 'DigitalTwin'

    src_fmu = OUTPUT_DIR / f"{fmu_name}.fmu"
    dst_fmu = OUTPUT_DIR / f"{model_name}.fmu"

    if src_fmu.exists() and src_fmu != dst_fmu:
        if dst_fmu.exists():
            dst_fmu.unlink()
        shutil.move(str(src_fmu), str(dst_fmu))
        print(f"\n  FMU saved as: output/{model_name}.fmu")

def validate_single_model(model_name):
    """Run strict validation on a single model. Returns True if valid."""
    model_dir = MODELS_DIR / model_name
    print(f"--- twinctl: Validating {model_name} ---")

    # 1. Structure Check
    checks = [
        (model_dir / "project.yaml", "Config file"),
        (model_dir / "src", "Source directory"),
        (model_dir / "test_data", "Test data directory"),
    ]

    failed = False
    for path, name in checks:
        if path.exists():
            print(f"  [OK]   {name}: Found")
        else:
            print(f"  [FAIL] {name}: Missing!")
            failed = True

    if failed:
        return False

    # 2. YAML Schema Validation
    config_file = model_dir / "project.yaml"
    try:
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"  [FAIL] project.yaml: Invalid YAML ({e})")
        return False

    def check_field(path, type_cls=None, allowed=None):
        """Helper to validate nested fields"""
        val = config
        for key in path.split('.'):
            val = val.get(key)
            if val is None:
                print(f"  [FAIL] Schema: Missing required field '{path}'")
                return False
        
        if type_cls and not isinstance(val, type_cls):
            print(f"  [FAIL] Schema: Field '{path}' must be {type_cls.__name__}, got {type(val).__name__}")
            return False
            
        if allowed and val not in allowed:
            print(f"  [FAIL] Schema: Field '{path}' has invalid value '{val}'. Allowed: {allowed}")
            return False
            
        return True

    schema_errors = 0
    
    # Required Sections
    for section in ['project', 'modelica', 'files', 'fmu']:
        if section not in config:
            print(f"  [FAIL] Schema: Missing section '{section}'")
            schema_errors += 1

    # Field Checks
    if not check_field('project.name', str): schema_errors += 1
    if not check_field('modelica.model_class', str): schema_errors += 1
    if not check_field('files.main', str): schema_errors += 1
    
    if not check_field('fmu.type', str, allowed=['cs', 'me']): schema_errors += 1
    if not check_field('fmu.platform', str, allowed=['static', 'dynamic', 'docker']): schema_errors += 1
    
    # Optional Validation Section
    if 'validation' in config:
        if not check_field('validation.active', bool): schema_errors += 1
        # Check numeric fields if present
        if 'tolerance' in config['validation'] and not isinstance(config['validation']['tolerance'], (int, float)):
             print(f"  [FAIL] Schema: Field 'validation.tolerance' must be number")
             schema_errors += 1

    # 3. Content Integrity Check
    if schema_errors == 0:
        print("  [OK]   Schema: Valid")
        
        # Check files.main existence
        main_path = config['files']['main']
        full_main_path = model_dir / "src" / main_path
        if full_main_path.exists():
             print(f"  [OK]   files.main: {main_path} (exists)")
        else:
             print(f"  [FAIL] files.main: {main_path} NOT FOUND in src/")
             schema_errors += 1
    
    if schema_errors > 0:
        print(f"\n{model_name} validation FAILED with {schema_errors} errors.")
        return False

    print(f"\n{model_name} is VALID and ready to build.")
    return True

def cmd_validate(args):
    """Validate model structure and configuration schema"""
    if args.all:
        models = get_available_models()
        if not models:
            print("No models found in input/models/")
            sys.exit(1)
        
        print(f"--- Validating all {len(models)} models ---\n")
        failed_count = 0
        for model in models:
            if not validate_single_model(model):
                failed_count += 1
            print("") # Spacer
            
        print(f"{'='*60}")
        if failed_count == 0:
            print(f"ALL {len(models)} models are VALID ✅")
        else:
            print(f"{failed_count}/{len(models)} models FAILED validation ❌")
            sys.exit(1)
            
    elif args.model:
        if not validate_single_model(args.model):
            sys.exit(1)
    else:
        print("Error: Specify a model name or use --all")
        print(f"Available models: {', '.join(get_available_models()) or 'none'}")
        sys.exit(1)

def cmd_template(args):
    """Generate a validation CSV template for a model"""
    if not args.model:
        print("Error: Specify a model name")
        print(f"Available models: {', '.join(get_available_models()) or 'none'}")
        sys.exit(1)

    model_dir = MODELS_DIR / args.model
    if not (model_dir / "project.yaml").exists():
        print(f"Error: Model '{args.model}' not found or missing project.yaml")
        sys.exit(1)

    print(f"--- Generating template for {args.model} ---")
    
    import yaml
    import csv
    
    with open(model_dir / "project.yaml") as f:
        config = yaml.safe_load(f)
    
    inputs = config.get('interface', {}).get('inputs', [])
    outputs = config.get('interface', {}).get('outputs', [])
    
    if not inputs:
        print("Warning: No inputs defined in project.yaml interface")
    
    # Create Header
    header = ['time'] + [i['name'] for i in inputs] + [o['name'] for o in outputs]
    
    # Create Default Row
    # Time = 0.0
    # Inputs = default or 0.0
    # Outputs = 0.0 (placeholder)
    row = [0.0]
    for i in inputs:
        row.append(i.get('start', 0.0)) # 'start' is sometimes used for default
    for o in outputs:
        row.append(0.0)
        
    out_dir = model_dir / "test_data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "validation_template.csv"
    
    with open(out_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(row)
        
    print(f"  Created: {out_file}")
    print("  Fill this file with your test data and rename to 'validation.csv' to use.")

def cmd_clean(args):
    """Clean up temporary build artifacts"""
    print("--- Cleaning artifacts ---")
    
    # Clean _active staging directory
    if ACTIVE_DIR.exists():
        try:
            shutil.rmtree(ACTIVE_DIR)
            print(f"  Removed: {ACTIVE_DIR}")
        except Exception as e:
            print(f"  Error removing {ACTIVE_DIR}: {e}")
    else:
        print(f"  Already clean: {ACTIVE_DIR} not found")

    # Clean build directory temporary files (but keep scripts)
    # We want to keep build_fmu.py and Dockerfile, but remove generated .mos
    generated_mos = ROOT_DIR / "build" / "generated_build.mos"
    if generated_mos.exists():
        try:
            generated_mos.unlink()
            print(f"  Removed: {generated_mos}")
        except Exception as e:
            print(f"  Error removing {generated_mos}: {e}")
            
    print("Done.")

def main():
    parser = argparse.ArgumentParser(
        description="twinctl - Digital Twin Factory Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 twinctl.py list                 List available models
  python3 twinctl.py build BiomassBoiler  Build a specific model
  python3 twinctl.py build --all          Build all models
  python3 twinctl.py validate --all       Validate all models
  python3 twinctl.py template BiomassBoiler Generate CSV template
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # list
    subparsers.add_parser("list", help="List available models")

    # build
    build_parser = subparsers.add_parser("build", help="Build FMU for a model")
    build_parser.add_argument("model", nargs="?", help="Model name from input/models/")
    build_parser.add_argument("--all", action="store_true", help="Build all models")

    # template
    template_parser = subparsers.add_parser("template", help="Generate validation CSV template")
    template_parser.add_argument("model", help="Model name")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Check model structure")
    validate_parser.add_argument("model", nargs="?", help="Model name to validate")
    validate_parser.add_argument("--all", action="store_true", help="Validate all models")

    # clean
    subparsers.add_parser("clean", help="Remove artifacts")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "template":
        cmd_template(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "clean":
        cmd_clean(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
