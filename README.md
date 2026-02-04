# Digital Twin FMU Builder - Production System

**Fully automated** FMU generation with **integrated Docker validation** and **CSV-based testing**.

## 🚀 Quick Start

1. Place client files in `input/src/`
2. Place validation CSV in `input/test_data/`
3. Run: `python build/split_validation_csv.py client_validation.csv`
4. Run: `.\twinctl build`
5. Get validated FMU from `output/`

## 📁 Folder Structure

```
build_mo/
├── input/
│   ├── project.yaml          # Config
│   ├── src/                  # ALL client files
│   │   ├── *.mo             # Modelica files
│   │   ├── PackageName/     # Package directories
│   │   └── data/            # Data files (.txt, .csv, .mat)
│   └── test_data/
│       ├── client_validation.csv  # Client provides
│       ├── test_inputs.csv        # Auto-generated
│       └── expected_outputs.csv   # Auto-generated
├── build/
│   ├── build_fmu.py               # Main automation
│   ├── split_validation_csv.py   # CSV splitter
│   ├── Dockerfile                 # Build + Test environment
│   └── generated_build.mos        # Auto-generated
├── output/
│   └── DigitalTwin.fmu           # VALIDATED FMU
└── tests/
    └── validate_fmu_docker.py    # In-container validation
```

## 📋 Complete Workflow

### Step 1: Client Sends Materials

You send: `CLIENT_QUESTIONNAIRE.md`

They provide ZIP with:
- `.mo` files (single or package directory)
- Data files (optional: `.txt`, `.csv`, `.mat`)
- **Validation CSV** (inputs + outputs from their test run)

### Step 2: Prepare Files

```bash
# Extract to input/src/
input/src/
├── MainModel/
│   ├── package.mo
│   ├── SubModel.mo
│   └── package.order
└── data/
    └── lookup_table.txt

# Place validation CSV
input/test_data/client_validation.csv
```

### Step 3: Split Validation CSV

```bash
python build/split_validation_csv.py client_validation.csv
```

**Output:**
```
Reading: client_validation.csv
Found 3 test scenarios
CSV columns: 17

Split complete!
  Created: test_inputs.csv (13 columns)
  Created: expected_outputs.csv (5 columns)

Ready for validation testing!
```

### Step 4: Configure project.yaml

Fill `input/project.yaml` from questionnaire:

```yaml
project:
  name: "BiomassBoiler_DigitalTwin"
  client: "Acme Corp"

validation:
  tolerance_percent: 5.0

modelica:
  model_class: "BiomassBoiler.DigitalTwin"
  language_version: "3.2.3"

files:
  main: "BiomassBoiler.mo"
```

### Step 5: Build + Validate (One Command!)

```bash
.\twinctl build
```

**What happens (all in Docker):**
```
1. Compile FMU from .mo files
2. Install Python + fmpy
3. Load test_inputs.csv
4. Run FMU with test inputs
5. Compare outputs with expected_outputs.csv
6. PASS/FAIL with tolerance check
7. Extract FMU only if PASS
```

**Output:**
```
[1/5] Loading project.yaml...
[2/5] Validating files...
[3/5] Generating OpenModelica script...
[4/5] Building Docker image (compiling FMU + validation)...
  Test data found - validation will run in container
  
  Running validation tests...
  [1/3] Time=0s
    PASS out_MW_gross: 59.2 (expected: 58.5, error: 1.2%)
    PASS out_Efficiency: 81.8 (expected: 82.0, error: 0.2%)
  
  VALIDATION PASSED
  All 3 test cases within ±5% tolerance

[5/5] Extracting validated FMU from image...

BUILD SUCCESS
FMU Location: output/DigitalTwin.fmu
FMU Size: 732.9 KB

Validation: PASSED (tested inside Docker)
  Tolerance: ±5.0%

FMU is ready for delivery!
```

### Step 6: Deliver

```
delivery_package/
├── DigitalTwin.fmu           # THE FMU (validated!)
├── project.yaml              # Config used
└── validation_report.txt     # PASS details
```

## 🔍 Key Features

✅ **Supports ANY file structure**:
- Single `.mo` files
- Package directories (`package.mo`, `package.order`)
- Data files (`.txt`, `.csv`, `.mat` for CombiTimeTable)

✅ **Client-friendly validation**:
- Send one CSV with inputs + outputs
- Auto-split into test cases
- Tolerance-based comparison

✅ **Integrated Build + Test**:
- Everything happens in Docker (no platform issues)
- FMU compiled and validated in same container
- Only delivered if tests PASS

✅ **Zero manual editing**:
- YAML configuration only
- Auto-generate build scripts
- One command builds + validates

## 🧪 Supported File Types

| Type | Extensions | Purpose |
|------|-----------|---------|
| Modelica | `.mo` | Model code |
| Package | `package.mo`, `package.order` | Structured libraries |
| Data | `.txt`, `.csv` | CombiTimeTable, lookup data |
| Data | `.mat` | MATLAB data files |
| Config | `.json`, `.xml` | External configuration |

## 📖 Requirements

- Docker Desktop (running)
- Python 3.x with:
  - `pyyaml`: `pip install pyyaml`
  - `fmpy` (for local testing): `pip install fmpy`

## 🎯 Production Checklist

For each client:

- [ ] Receive questionnaire + files
- [ ] Extract to `input/src/`
- [ ] Place validation CSV in `input/test_data/`
- [ ] Split CSV: `python build/split_validation_csv.py client_validation.csv`
- [ ] Create `input/project.yaml`
- [ ] Build + Validate: `.\twinctl build`
- [ ] Verify PASS status
- [ ] Deliver FMU

## 💡 Troubleshooting

**Build fails during validation:**
- Check tolerance in `project.yaml` (increase if needed)
- Review expected outputs (client data might be approximations)
- Check FMU variable names match `interface.outputs` config

**Missing columns warning:**
- Update `project.yaml` interface section
- Or provide complete validation CSV

**File not found errors:**
- Ensure all referenced data files are in `input/src/`
- Check package directory structure

---

**System is production-ready for enterprise digital twin deployment!** 🚀
