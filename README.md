# Digital Twin FMU Builder Template - YAML-Based

Automated FMU generation system for converting client Modelica models into FMUs for digital twin deployment.

## 🚀 Quick Start

1. **Place client `.mo` files** in `input/src/`
2. **Create/edit** `project.yaml` (use `project.yaml.example` as template)
3. **Run**: `python build/build_fmu.py`
4. **Get FMU** from `output/` directory

## 📁 Structure

```
build_mo/
├── project.yaml           # PROJECT CONFIG (edit this!)
├── project.yaml.example   # Template with all options
├── input/src/             # Client .mo files
├── build/
│   ├── build_fmu.py       # Automation script
│   ├── Dockerfile         # OpenModelica environment
│   └── generated_build.mos # Auto-generated (don't edit)
└── output/                # Generated FMUs
```

## ⚙️ Configuration

Edit `project.yaml`:

```yaml
project:
  name: "YourProject"

modelica:
  model_class: "PackageName.ModelName"  # REQUIRED

files:
  main: "MainFile.mo"  # REQUIRED
  dependencies: []      # Optional: additional .mo files

fmu:
  type: "cs"           # co-simulation
  version: "2.0"
  platform: "static"
  output_name: "YourFMU"
```

See `project.yaml.example` for all options including external libraries.

## 🔍 Features

- ✅ **Zero manual editing**: No touching Dockerfiles or scripts
- ✅ **YAML validation**: Catches errors before building
- ✅ **Dynamic script generation**: `build.mos` created automatically
- ✅ **External library support**: Load additional packages
- ✅ **CI/CD ready**: One command to build

## 📋 Requirements

- Docker Desktop (running)
- Python 3.x with PyYAML (`pip install pyyaml`)

## 📖 For New Clients

Send them `CLIENT_QUESTIONNAIRE.md` to collect model details, then fill in `project.yaml` accordingly.
