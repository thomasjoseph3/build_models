# Digital Twin FMU Builder - Zero-Code Production System 🏭

A fully automated, **Zero-Code** system for building and validating Functional Mock-up Units (FMUs).

**Key Features:**
*   **Zero-Code:** Add models by copy-pasting folders.
*   **Fail Fast:** `twinctl validate` catches errors instantly.
*   **Dockerized:** Consistent builds across Windows/Linux/Mac.
*   **Multi-Version:** Supports legacy (v1.19) and modern (v1.25) OpenModelica versions.
*   **Automated Validation:** Every FMU is simulated and tested before delivery.

---

## 🚀 Quick Start

### 1. Requirements
*   **Docker Desktop** (Running)
*   **Python 3.10+**
*   **Libraries:** `pip install pyyaml`

### 2. Basic Commands
The `twinctl.py` script is your control center.

```bash
# List available models
python3 twinctl.py list

# Validate ALL models (Check structure & config)
python3 twinctl.py validate --all

# Build ALL models (Compiles & Validates in Docker)
python3 twinctl.py build --all
```

### 3. Add a New Model
1.  Create a folder: `input/models/MyNewModel/`
2.  Add your source code: `input/models/MyNewModel/src/`
3.  Add a config file: `input/models/MyNewModel/project.yaml`
4.  (Optional) Add test data: `input/models/MyNewModel/test_data/validation.csv`

---

## 📁 Directory Structure

```
build_models/
├── input/
│   └── models/
│       ├── BiomassBoiler/      # A complete model package
│       │   ├── project.yaml    # Configuration
│       │   ├── src/            # Source code (.mo files)
│       │   └── test_data/      # validation.csv
│       └── ShellAndTube/       # Another model
│
├── output/                     # Generated FMUs appear here
├── build/                      # System internals (do not touch)
└── twinctl.py                  # Main CLI tool
```

---

## ⚙️ Configuration (project.yaml)

Every model needs a `project.yaml`. Here is the strict schema:

```yaml
project:
  name: "MyModel_DigitalTwin"
  description: "A great model"

modelica:
  model_class: "MyPackage.ModelName"  # The entry point
  msl_version: "4.0.0"

fmu:
  output_name: "MyModel"      # Result: MyModel.fmu
  type: "cs"                  # cs (Co-Simulation) or me (Model Exchange)
  platform: "docker"
  # Optional: Specify exact OpenModelica version
  builder_image: "openmodelica/openmodelica:v1.25.1-minimal"

files:
  main: "MyPackage/package.mo"  # Path inside src/

validation:
  active: true
  tolerance: 5.0  # Allow +/- 5.0 absolute error
  step_size: 0.1  # Simulation step size (seconds)

interface:
  inputs:
    - name: "u_input1"
  outputs:
    - name: "y_output1"
```

---

## 🧪 Validation Workflow

The system provides two layers of protection:

1.  **Structural Validation (`twinctl validate`)**
    *   Runs on your host machine.
    *   Checks if files exist.
    *   Checks if YAML configuration is valid.
    *   **Always run this first!**

2.  **Functional Validation (`twinctl build`)**
    *   Runs inside the Docker container.
    *   Compiles the FMU.
    *   Loads `validation.csv`.
    *   Simulates the FMU using the CSV inputs.
    *   Compares FMU outputs vs CSV outputs.
    *   **If validation fails, the build aborts.**

---

## 🛠️ Advanced Usage

### Generate Validation Template
Don't know how to format your CSV? Let the system help.

```bash
python3 twinctl.py template MyNewModel
# Creates: input/models/MyNewModel/test_data/validation_template.csv
```

### Clean Artifacts
Free up disk space by removing temporary files.

```bash
python3 twinctl.py clean
```
