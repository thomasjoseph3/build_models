#!/usr/bin/env python3
"""
twinctl - The Digital Twin Factory Controller
Unified CLI for building, testing, and managing FMU projects.
"""
import argparse
import sys
import subprocess
import shutil
import os
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).parent.absolute()
INPUT_DIR = ROOT_DIR / "input"
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

def cmd_build(args):
    """Build the Docker image and FMU"""
    print("--- twinctl: Building Digital Twin FMU ---")
    run_command(f"{sys.executable} build/build_fmu.py")

def cmd_validate(args):
    """Run validation tests"""
    print("--- twinctl: Validating Project Structure ---")
    
    checks = [
        (INPUT_DIR / "project.yaml", "Config file"),
        (INPUT_DIR / "src", "Source directory"),
        (INPUT_DIR / "test_data" / "client_validation.csv", "Validation data")
    ]
    
    failed = False
    for path, name in checks:
        if path.exists():
            print(f"  [OK]   {name}: {path.name}")
        else:
            print(f"  [FAIL] {name}: Missing!")
            failed = True
            
    if failed:
        sys.exit(1)
    print("\nStructure is valid.")

def cmd_clean(args):
    """Clean build artifacts"""
    print("--- twinctl: Cleaning workspace ---")
    
    fmu_path = OUTPUT_DIR / "DigitalTwin.fmu"
    if fmu_path.exists():
        fmu_path.unlink()
        print(f"Removed: {fmu_path}")
    else:
        print("Nothing to clean.")

def cmd_shell(args):
    """Enter the builder container shell (debugging)"""
    print("--- twinctl: Entering Docker Shell ---")
    run_command("docker run --rm -it -v src:/build/input/src fmu-builder /bin/bash")

def main():
    parser = argparse.ArgumentParser(description="twinctl - Digital Twin Factory Controller")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # build
    subparsers.add_parser("build", help="Build and validate the FMU")
    
    # validate
    subparsers.add_parser("validate", help="Check project structure")
    
    # clean
    subparsers.add_parser("clean", help="Remove artifacts")
    
    # debug
    subparsers.add_parser("shell", help="Open debug shell in Docker")

    args = parser.parse_args()
    
    if args.command == "build":
        cmd_build(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "shell":
        cmd_shell(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
