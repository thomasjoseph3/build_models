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

def sync_project(project_name):
    """Sync project files to input directory"""
    project_dir = ROOT_DIR / "projects" / project_name
    
    if not project_dir.exists():
        print(f"Error: Project '{project_name}' not found in projects/ directory.")
        sys.exit(1)
        
    print(f"--- Loading Project: {project_name} ---")
    
    # Clean input
    if INPUT_DIR.exists():
        shutil.rmtree(INPUT_DIR)
    INPUT_DIR.mkdir()
    
    # Copy files
    try:
        if (project_dir / "src").exists():
            shutil.copytree(project_dir / "src", INPUT_DIR / "src")
        else:
            print("Warning: No src/ folder in project")
            
        if (project_dir / "test_data").exists():
            shutil.copytree(project_dir / "test_data", INPUT_DIR / "test_data")
            
        if (project_dir / "project.yaml").exists():
            shutil.copy(project_dir / "project.yaml", INPUT_DIR / "project.yaml")
        else:
            print("Error: project.yaml missing in project folder")
            sys.exit(1)
            
        print(f"Files staged to input/")
    except Exception as e:
        print(f"Error syncing files: {e}")
        sys.exit(1)

def save_artifact(project_name):
    """Save built FMU back to project folder"""
    project_out = ROOT_DIR / "projects" / project_name / "output"
    project_out.mkdir(parents=True, exist_ok=True)
    
    fmu_src = OUTPUT_DIR / "DigitalTwin.fmu"
    if fmu_src.exists():
        timestamp = subprocess.check_output("powershell Get-Date -Format 'yyyyMMdd_HHmm'", shell=True).decode().strip()
        fmu_name = f"{project_name}_{timestamp}.fmu"
        shutil.copy(fmu_src, project_out / fmu_name)
        print(f"--- Archived to: projects/{project_name}/output/{fmu_name} ---")

def cmd_build(args):
    """Build the Docker image and FMU"""
    if args.project:
        sync_project(args.project)
        
    print("--- twinctl: Building Digital Twin FMU ---")
    run_command(f"{sys.executable} build/build_fmu.py")
    
    if args.project:
        save_artifact(args.project)

def cmd_validate(args):
    """Run validation tests"""
    if args.project:
        sync_project(args.project)
        
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

# ... existing clean/shell commands ...

def cmd_init(args):
    """Create a new project from template"""
    if not args.name:
        print("Error: Please specify project name with --name")
        sys.exit(1)
        
    target_dir = ROOT_DIR / "projects" / args.name
    if target_dir.exists():
        print(f"Error: Project '{args.name}' already exists.")
        sys.exit(1)
        
    template_dir = ROOT_DIR / "projects" / "_template"
    if not template_dir.exists():
        print("Error: Template directory missing.")
        sys.exit(1)
        
    try:
        shutil.copytree(template_dir, target_dir)
        print(f"--- Created Project: {args.name} ---")
        print(f"Location: projects/{args.name}")
        print("Structure:")
        print(f"  src/model/      <-- Put .mo files here")
        print(f"  src/libraries/  <-- Put external libs here")
        print(f"  src/data/       <-- Put .txt/.csv data here")
        print(f"  project.yaml    <-- Edit config")
    except Exception as e:
        print(f"Error creating project: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="twinctl - Digital Twin Factory Controller")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-p", "--project", help="Name of project in projects/ folder")
    
    # init
    parser_init = subparsers.add_parser("init", help="Create new project")
    parser_init.add_argument("-n", "--name", required=True, help="Project name")
    
    # build
    subparsers.add_parser("build", parents=[parent_parser], help="Build and validate the FMU")
    
    # validate
    subparsers.add_parser("validate", parents=[parent_parser], help="Check project structure")
    
    # clean
    subparsers.add_parser("clean", help="Remove artifacts")
    
    # debug
    subparsers.add_parser("shell", help="Open debug shell in Docker")

    args = parser.parse_args()
    
    if args.command == "init":
        cmd_init(args)
    elif args.command == "build":
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
