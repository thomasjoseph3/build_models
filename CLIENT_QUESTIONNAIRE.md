# Client Intake Questionnaire - FMU Generation

Please provide the following information so we can build your Digital Twin FMU.

## 1. Project Information

**Project Name**: ___________________________

**Brief Description**: ___________________________

## 2. Model Details

**Main Model Class** (full path, e.g., `MyPackage.Simulation.MainModel`):  
___________________________

**Modelica Language Version** (if known): ___________________________

## 3. Files to Provide

Please send us the following files in a ZIP archive:

- [ ] Main `.mo` file(s)
- [ ] Any additional dependency `.mo` files
- [ ] External libraries (if applicable)

## 4. External Libraries (Optional)

Does your model use any external libraries beyond the standard Modelica library?

- [ ] No
- [ ] Yes - please list:

| Library Name | Version | Notes |
|--------------|---------|-------|
|              |         |       |

## 5. Interface Specification

### Inputs (Controls)
*List the variables we should be able to change at runtime.*

| Variable Name | Description | Unit |
|---------------|-------------|------|
|               |             |      |

### Outputs (Sensors)
*List the variables you need to monitor/log.*

| Variable Name | Description | Unit |
|---------------|-------------|------|
|               |             |      |

## 6. FMU Configuration

**FMU Type**:
- [ ] Co-Simulation (recommended for digital twins)
- [ ] Model Exchange

**Target Platform**:
- [ ] Linux64 (Docker/Cloud deployment)
- [ ] Windows64

**Preferred Solver** (optional): ___________________________

## 7. Delivery

Once we receive your files and this completed questionnaire, we will:
1. Generate a `project.yaml` configuration
2. Build and test the FMU
3. Deliver the compiled `.fmu` file with documentation

**Expected Delivery**: 2-3 business days from receipt of complete information
