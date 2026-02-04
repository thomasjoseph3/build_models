# Client Intake Questionnaire - FMU Generation

Please provide the following information so we can build your Digital Twin FMU.

## 1. Project Information

**Project Name**: ___________________________

**Brief Description**: ___________________________

**Contact Person**: ___________________________

## 2. Model Details

**Main Model Class** (full path, e.g., `MyPackage.Simulation.MainModel`):  
___________________________

**Modelica Language Version** used to develop the model:
- [ ] 3.2.x (specify: _________)
- [ ] 3.4
- [ ] 4.0
- [ ] Other: ___________

**Modelica Standard Library (MSL) Version** used:
- [ ] Default (let us decide)
- [ ] 3.2.3
- [ ] 4.0.0
- [ ] Other: ___________

## 3. Files to Provide

Please send us the following files in a **ZIP archive**:

### Required:
- [ ] **Modelica files** (`.mo`)
  - Single file OR
  - Package directory structure (with `package.mo`, `package.order`)
  - *Note: If your model depends on other separate .mo files, please include them all and list the load order.*
  - *Example: `import Modelica.Fluid.Pipes.StaticPipe;`*
  
### Optional but Recommended:
- [ ] **Data files** (if model uses external data):
  - `.txt`, `.csv` - CombiTimeTable data
  - `.mat` - MATLAB data files
  - `.json`, `.xml` - Configuration files
  
- [ ] **Validation data** (see Section 7 below)
- [ ] **Documentation** (model description, usage notes)

**Example File Structure:**
```
your_project.zip
├── src/
│   ├── MainModel/
│   │   ├── package.mo
│   │   ├── SubModel1.mo
│   │   ├── SubModel2.mo
│   │   └── package.order
│   └── data/
│       └── lookup_table.txt
└── test_data/
    └── validation_data.csv
```

## 4. External Libraries

Does your model use any external libraries beyond the standard Modelica library?

- [ ] No
- [ ] Yes - please list below:

| Library Name | Version | Purpose | Included? |
|--------------|---------|---------|-----------|
|              |         |         | Yes / No  |

**Note:** If yes, please include the library source code or provide installation instructions.

## 5. Interface Specification

### Inputs (Controls)
*List all variables that should be controllable at runtime.*

| Variable Name | Description | Unit | Typical Range | Default Value |
|---------------|-------------|------|---------------|---------------|
| Example: pump_speed | Pump RPM | rpm | 0-3000 | 1500 |
|               |             |      |               |               |

### Outputs (Sensors/Measurements)
*List all variables you need to monitor/log.*

| Variable Name | Description | Unit | Expected Range |
|---------------|-------------|------|----------------|
| Example: flow_rate | Water flow | m³/h | 0-500 |
|               |             |      |                |

### Parameters (Static Configuration)
*List variables that are set once before simulation starts.*

| Parameter Name | Description | Unit | Value |
|---------------|-------------|------|-------|
|               |             |      |       |

## 6. FMU Configuration

**FMU Type**:
- [x] Co-Simulation (recommended for digital twins)
- [ ] Model Exchange

**Target Platform**:
- [x] Linux64 (Docker/Cloud deployment - recommended)
- [ ] Windows64
- [ ] Static (platform-independent)

**Preferred Solver** (optional):
- [x] CVODE (recommended - handles stiff systems)
- [ ] Euler (simple/fast - for non-stiff models)
- [ ] IDA (for differential-algebraic equations)
- [ ] DASSL (alternative stiff solver)
- [ ] Runge-Kutta (moderate complexity)
- [ ] Let you decide (we'll choose based on model type)

**Solver Tolerance** (optional):
- Default: `1e-6` (recommended)
- Custom: ___________ (lower = more accurate but slower)

**Simulation Time Frame** (for testing):
- Typical simulation duration: _________ seconds/hours
- Recommended step size: _________ seconds

## 7. Test & Validation Data ⭐ **REQUIRED**

**IMPORTANT**: Provide validation data to ensure FMU correctness!

### Option A: Combined Validation CSV (Recommended)
Provide a **single CSV file** with inputs AND expected outputs from a simulation you've already run:

**File**: `validation_data.csv`

```csv
time,input1,input2,output1,output2
0,100,20,250,85
60,110,22,275,87
120,120,25,300,90
```

**We will automatically split this into test inputs and expected outputs.**

### Option B: Separate CSVs
Provide two separate files:

**`test_inputs.csv`**:
```csv
time,input1,input2
0,100,20
60,110,22
```

**`expected_outputs.csv`**:
```csv
time,output1,output2
0,250,85
60,275,87
```

### Validation Tolerance
What tolerance is acceptable for output comparison?
- [ ] ±1%
- [ ] ±5% (recommended)
- [ ] ±10%
- [ ] Other: ___________

**Test Scenario Description**:
_______________________________________________________________
_______________________________________________________________

## 8. Delivery

Once we receive your files and this completed questionnaire, we will:
1. Generate `project.yaml` configuration
2. Build the FMU (inside Docker)
3. **Run validation tests** (inside Docker)
4. Provide validation report (Pass/Fail)
5. Deliver FMU + documentation

**Expected Delivery**: 2-3 business days from receipt of complete information

**Delivery Package**:
- [x] `.fmu` file
- [x] Validation report (PASS/FAIL)
- [x] `project.yaml` (configuration used)
- [ ] Full package with test scripts (optional)
