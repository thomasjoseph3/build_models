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
ROOT_DIR = Path(__file__).parent.absolute()
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

    # Clean active directory
    if ACTIVE_DIR.exists():
        shutil.rmtree(ACTIVE_DIR)
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
                results[model] = "FAIL"
                print(f"\nWARNING: Build failed for {model}, continuing...\n")

        # Summary
        print(f"\n{'='*60}")
        print("BUILD SUMMARY")
        print(f"{'='*60}")
        for model, status in results.items():
            icon = "✅" if status == "PASS" else "❌"
            print(f"  {icon} {model}: {status}")
        
        failed = sum(1 for s in results.values() if s == "FAIL")
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

        stage_model(args.model)
        print(f"--- twinctl: Building {args.model} FMU ---")
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

def cmd_validate(args):
    """Validate model structure"""
    if not args.model:
        print("Error: Specify a model name")
        print(f"Available models: {', '.join(get_available_models()) or 'none'}")
        sys.exit(1)

    model_dir = MODELS_DIR / args.model
    print(f"--- twinctl: Validating {args.model} ---")

    checks = [
        (model_dir / "project.yaml", "Config file"),
        (model_dir / "src", "Source directory"),
        (model_dir / "test_data", "Test data directory"),
    ]

    failed = False
    for path, name in checks:
        if path.exists():
            print(f"  [OK]   {name}: {path.name}")
        else:
            print(f"  [FAIL] {name}: Missing!")
            failed = True

    # Check for .mo files
    mo_files = list((model_dir / "src").rglob("*.mo")) if (model_dir / "src").exists() else []
    if mo_files:
        print(f"  [OK]   Modelica files: {len(mo_files)} found")
    else:
        print(f"  [FAIL] Modelica files: None found in src/")
        failed = True

    if failed:
        sys.exit(1)
    print(f"\n{args.model} structure is valid.")

def cmd_clean(args):
    """Remove build artifacts"""
    print("--- twinctl: Cleaning ---")
    
    # Clean active staging
    if ACTIVE_DIR.exists():
        shutil.rmtree(ACTIVE_DIR)
        print("  Cleaned: input/_active/")

    # Clean output
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.iterdir():
            f.unlink()
            print(f"  Removed: output/{f.name}")
    
    print("Done.")

def main():
    parser = argparse.ArgumentParser(
        description="twinctl - Digital Twin Factory Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 twinctl.py list                 List available models
  python3 twinctl.py build BiomassBoiler  Build a specific model
  python3 twinctl.py build --all          Build all models
  python3 twinctl.py validate BiomassBoiler  Check model structure
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # list
    subparsers.add_parser("list", help="List available models")

    # build
    build_parser = subparsers.add_parser("build", help="Build FMU for a model")
    build_parser.add_argument("model", nargs="?", help="Model name from input/models/")
    build_parser.add_argument("--all", action="store_true", help="Build all models")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Check model structure")
    validate_parser.add_argument("model", help="Model name to validate")

    # clean
    subparsers.add_parser("clean", help="Remove artifacts")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "clean":
        cmd_clean(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
