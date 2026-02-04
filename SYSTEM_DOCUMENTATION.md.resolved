# FMU Build System - Technical Documentation

**Version:** 2.0  
**System Type:** Automated Digital Twin FMU Generator  
**Target Users:** Engineering teams delivering validated FMUs to clients

---

## Executive Summary

This system automates the complete FMU (Functional Mock-up Unit) build pipeline, from receiving client Modelica files to delivering a validated, production-ready FMU. It ensures consistency, eliminates manual compilation steps, and guarantees quality through automated validation testing.

---

## 1. What We Expect from Clients

### 1.1 Required Materials

Clients must provide:

| Item | Format | Purpose |
|------|--------|---------|
| **Modelica Source Files** | [.mo](file:///c:/Users/tj089/Desktop/build_fmu/build_mo/input/src/BiomassBoiler.mo) files | The physics model to compile into FMU |
| **Validation Data** | Single CSV file | Input/output data proving the model works correctly |
| **Configuration Data** | Filled questionnaire | Model metadata (I/O specs, solver preferences, tolerances) |

### 1.2 Optional Materials

| Item | Purpose |
|------|---------|
| External Libraries | If model depends on non-standard Modelica libraries |
| Data Files | [.csv](file:///c:/Users/tj089/Desktop/build_fmu/build_mo/input/test_data/test_inputs.csv), `.txt`, `.mat` files used by `CombiTimeTable` or similar |

### 1.3 Standard File Structure (Client Delivery)

We enforce a standard intake structure. Clients send files organized as:

```
client_delivery.zip
├── model/               # All .mo files (single or multiple)
│   └── TheirModel.mo
├── libraries/           # External Modelica libraries (optional)
│   └── SomeLib/
├── data/                # CSV/TXT data files (optional)
│   └── lookup.csv
└── validation.csv       # Combined input + expected output data
```

**Why this structure?**
- Works for simple projects (1 file) and complex projects (100+ files)
- No conditional logic needed in our build system
- Empty folders are allowed - the system ignores them

---

## 2. How We Process Client Files

### 2.1 Ingestion Workflow

1. **Receive ZIP** from client
2. **Extract contents** into `input/src/` following the standard structure:
   ```
   input/src/model/       ← Extract client's model/ folder here
   input/src/libraries/   ← Extract client's libraries/ folder here
   input/src/data/        ← Extract client's data/ folder here
   ```
3. **Place validation CSV** in `input/test_data/client_validation.csv`
4. **Configure** `input/project.yaml` based on questionnaire responses

### 2.2 Directory Layout (Our System)

```
build_mo/
├── input/                      # Client workspace (single source of truth)
│   ├── project.yaml            # Build configuration
│   ├── src/
│   │   ├── model/              # Client .mo files
│   │   ├── libraries/          # External Modelica libs
│   │   └── data/               # Data files for CombiTimeTable
│   └── test_data/
│       └── client_validation.csv
│
├── output/                     # Delivered FMU appears here
│   └── DigitalTwin.fmu
│
├── build/                      # System internals (DO NOT TOUCH)
│   ├── build_fmu.py            # Main orchestrator
│   ├── Dockerfile              # Build environment definition
│   └── split_validation_csv.py # CSV splitter
│
├── tests/
│   └── validate_fmu_docker.py  # Validation logic (runs in Docker)
│
└── twinctl.bat                # CLI interface
```

---

## 3. Build Process (Internals)

### 3.1 Build Pipeline

When you run `twinctl build`, the following happens:

```
[Step 1] Load project.yaml
         ↓
[Step 2] Validate file structure
         ↓
[Step 3] Generate OpenModelica build script (build.mos)
         ↓
[Step 4] Auto-split client_validation.csv → test_inputs.csv + expected_outputs.csv
         ↓
[Step 5] Build Docker Image
         ├── Install OpenModelica v1.24.0
         ├── Copy input/src/ → /build/input/src/
         ├── Compile FMU using build.mos
         ├── Install Python + fmpy
         ├── Run validation tests (if test data exists)
         └── Exit with error if validation fails
         ↓
[Step 6] Extract FMU from Docker image → output/DigitalTwin.fmu
         ↓
[SUCCESS] Deliver FMU to client
```

### 3.2 Validation Logic

**Auto-Split CSV:**
- Input: `client_validation.csv` (combined inputs + outputs)
- Output: `test_inputs.csv` (time + input columns)
- Output: `expected_outputs.csv` (time + output columns)

**Validation Process (Inside Docker):**
1. Load `test_inputs.csv`
2. Run FMU simulation for each test scenario
3. Compare actual outputs vs. `expected_outputs.csv`
4. Check if all errors are within tolerance (default: ±5%)
5. **If PASS:** Extract FMU
6. **If FAIL:** Abort build and report which outputs failed

---

## 4. System Features

### 4.1 Universal File Support

✅ **Single `.mo` file**  
✅ **Multiple `.mo` files**  
✅ **Package structures** (`package.mo`, `package.order`)  
✅ **External libraries** (any Modelica library)  
✅ **Data files** (`.csv`, `.txt`, `.mat`)  
✅ **Mixed complexity** (all above combined)

### 4.2 Automated Quality Gates

✅ **Automated CSV splitting** - No manual preprocessing  
✅ **In-container validation** - Tests run in same environment as compilation  
✅ **Tolerance-based comparison** - Configurable acceptable error (default ±5%)  
✅ **PASS/FAIL gate** - FMU only delivered if validation succeeds  

### 4.3 Cross-Platform Compatibility

✅ **Windows CLI** - `twinctl.bat`  
✅ **Linux/Mac CLI** - `twinctl.py`  
✅ **CI/CD Ready** - All commands scriptable  
✅ **Docker-based** - No local OpenModelica installation required  

### 4.4 Configurability

via `project.yaml`:
- ✅ **Modelica version** (via Docker image tag)
- ✅ **FMU type** (Co-Simulation or Model Exchange)
- ✅ **Platform** (Static, Linux64, Win64)
- ✅ **Solver** (Default: CVODE)
- ✅ **Tolerance** (Validation tolerance percentage)
- ✅ **I/O Interface** (Define inputs/outputs for validation)

---

## 5. Flexibility & Extensibility

### 5.1 Handling Edge Cases

| Scenario | How System Handles It |
|----------|----------------------|
| No external libraries | `input/src/libraries/` stays empty - no error |
| No validation data | Build succeeds but prints warning "No validation performed" |
| Multiple dependencies | List them in `project.yaml` → `files.dependencies[]` |
| Old Modelica version | Change Docker image in `Dockerfile` (e.g., `v1.19.0`) |

### 5.2 Adding New Features

**Want to add pre-processing?**
1. Add step in `build_fmu.py` before Docker call
2. Example: Convert client's `.mat` file to `.csv`

**Want to change validation logic?**
1. Edit `tests/validate_fmu_docker.py`
2. Example: Add custom physics checks

**Want to archive builds?**
1. Add timestamp to output filename after extraction
2. Move to `archive/` folder

---

## 6. How to Use the System

### 6.1 One-Time Setup

```powershell
# Install Docker Desktop
# Ensure Python 3.x installed with PyYAML
pip install pyyaml
```

### 6.2 For Each Client

```powershell
# 1. Clear previous client data
del /Q input\src\model\*
del /Q input\src\libraries\*
del /Q input\src\data\*

# 2. Extract client files into input/src/
# (manually organize into model/, libraries/, data/)

# 3. Place validation CSV
copy client_data\validation.csv input\test_data\client_validation.csv

# 4. Edit input\project.yaml
# (update model_class, inputs, outputs, tolerance)

# 5. Build FMU
.\twinctl build

# 6. Deliver
# FMU is in output\DigitalTwin.fmu
```

---

## 7. Technical Architecture

### 7.1 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | Python 3.x | Build pipeline control |
| **Compilation** | OpenModelica 1.24.0 | Modelica → FMU conversion |
| **Containerization** | Docker | Reproducible build environment |
| **Validation** | Python + fmpy | FMU simulation & testing |
| **CLI** | Batch + Python | User interface |

### 7.2 Why Docker?

- **Consistency:** Same Linux environment regardless of host OS
- **Isolation:** Client A's libs don't affect Client B
- **Versioning:** Lock OpenModelica version (avoids "works on my machine")
- **CI/CD:** Jenkins/GitHub Actions can run identical builds

### 7.3 Data Flow

```
Client Files
    ↓
[input/src/] (Standardized structure)
    ↓
[Docker Container] (Isolated build + test)
    ↓
[FMU Validation] (Quality gate)
    ↓
[output/DigitalTwin.fmu] (Deliverable)
```

---

## 8. Maintenance & Troubleshooting

### 8.1 Common Issues

**Build fails with "FMU not created"**
- Check `build_output.log` in Docker logs
- Usually: syntax error in `.mo` file or missing dependency

**Validation fails**
- Check tolerance in `project.yaml` (increase if needed)
- Verify client's expected outputs are correct
- Review variable names match `interface.outputs`

**Docker errors**
- Ensure Docker Desktop is running
- Run `docker system prune` to free space

### 8.2 Upgrading OpenModelica

```dockerfile
# In build/Dockerfile, change:
FROM openmodelica/openmodelica:v1.24.0-minimal
# To:
FROM openmodelica/openmodelica:v1.25.0-minimal
```

---

## 9. Security & Best Practices

### 9.1 Client Data Handling

- ⚠️ `input/` contains sensitive client IP - do not commit to version control
- ✅ Add `input/` to `.gitignore`
- ✅ Archive client data separately after delivery

### 9.2 Version Control Strategy

**Track:**
- `build/` (build scripts)
- `tests/` (validation logic)
- `twinctl.py` (CLI tool)
- `README.md`, `CLIENT_QUESTIONNAIRE.md`

**Do NOT track:**
- `input/` (client data)
- `output/` (generated FMUs)
- Docker images

---

## 10. Future Enhancements

**Roadmap:**
- [ ] Web UI for project.yaml configuration
- [ ] Jenkins pipeline integration
- [ ] Automated client data staging from SharePoint
- [ ] Multi-FMU batch processing
- [ ] Model comparison reports (v1 vs v2)
- [ ] Performance benchmarking suite

---

## Summary

This system transforms FMU delivery from a manual, error-prone process into a reliable, automated pipeline. By enforcing a standard directory structure and validating every build, we ensure consistent quality and reduce turnaround time from days to minutes.

**Key Principles:**
1. **Single source of truth:** `input/` directory
2. **Standard structure:** `model/`, `libraries/`, `data/` - always
3. **Automated validation:** Every FMU is tested before delivery
4. **Docker isolation:** Reproducible builds across any machine
