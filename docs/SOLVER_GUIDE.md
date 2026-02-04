# Solver Configuration Documentation

## How Solvers Work in FMUs

### FMU Types and Solver Location

**Co-Simulation FMU** (what we build):
- Solver is **compiled into the FMU**
- You choose solver at **build time** (in project.yaml)
- Cannot change solver after FMU is built
- Example: `solver: "cvode"` in YAML → CVODE embedded in FMU binary

**Model Exchange FMU** (alternative):
- NO solver in FMU
- You provide solver at **runtime** (in Python/MATLAB)
- Full flexibility to switch solvers

### Our Implementation

**Configuration** (`project.yaml`):
```yaml
fmu:
  solver: "cvode"      # Solver to embed
  tolerance: 1e-6      # Accuracy setting
```

**Available Solvers** (OpenModelica):
- `cvode` - **Recommended** for most models (handles stiff systems)
- `euler` - Simple, fast (for non-stiff models only)
- `ida` - For differential-algebraic equations (DAEs)
- `dassl` - Alternative stiff solver
- `rungekutta` - Good accuracy/speed balance

### Solver Choice Flowchart

```
Is your model STIFF? (rapid changes, multiple timescales)
  ├─ YES → Use "cvode" (default)
  └─ NO  → Is it simple/linear?
      ├─ YES → Use "euler" (faster)
      └─ NO  → Use "cvode" (safe choice)

Has algebraic constraints? (e.g., 0 = f(x))
  └─ YES → Use "ida" or "dassl"
```

### Runtime Control (What You CAN Change)

Even with fixed solver, you control:
```python
fmu.setupExperiment(
    tolerance=1e-6,      # ✅ Override build tolerance
    stepSize=0.1         # ✅ Communication step
)
```

**Note**: `tolerance` in `setupExperiment()` may override compile-time setting depending on OpenModelica version.

### Rebuild to Change Solver

To switch from CVODE to Euler:
1. Edit `input/project.yaml`: `solver: "euler"`
2. Run: `python build/build_fmu.py`
3. New FMU with Euler solver delivered

**Build time**: ~4 minutes (same as before)

### Solver Performance Comparison

| Solver | Speed | Accuracy | Best For |
|--------|-------|----------|----------|
| cvode  | Medium | High | Stiff systems, default choice |
| euler  | Fast | Low | Simple, non-stiff models |
| ida    | Slow | High | DAE systems |
| dassl  | Medium | High | Alternative to CVODE |
| rungekutta | Medium | Medium | Balanced performance |

### For BiomassBoiler

**Recommendation**: `cvode` with `tolerance: 1e-6`

**Why**:
- Boiler has multiple timescales (fast: pressure, slow: temperature)
- Non-linear combustion dynamics
- CVODE handles this well

**Alternative**: If speed is critical and accuracy can be lower, try `euler` with smaller step sizes.

## Current Setup Status

✅ **Solver configuration implemented**:
- Added to `project.yaml` schema
- Build script passes solver to OpenModelica
- Questionnaire asks client for preference
- Example template includes solver options
- Default: CVODE with 1e-6 tolerance

⚙️ **Note**: OpenModelica solver API may need adjustment based on version compatibility.
