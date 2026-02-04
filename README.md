# FMU Build Experiment - Standard Structure

This folder demonstrates building FMUs from Modelica source code using OpenModelica in Docker.

## 📁 Folder Structure

```
build_mo/
├── src/                    # Source files
│   └── BiomassBoiler.mo   # Modelica package with DigitalTwin model
├── build/                  # Build configuration
│   ├── Dockerfile         # Docker build environment
│   └── build.mos          # OpenModelica build script
├── output/                 # Generated FMUs
│   └── DigitalTwin.fmu    # Compiled FMU (733 KB)
├── tests/                  # Test scripts
│   ├── test_fmu.py        # Simple validation test
│   └── simulate_fmu.py    # Full simulation demo
└── README.md              # This file
```

## 🚀 Quick Start

### Build the FMU

```bash
cd build
docker build -t fmu-builder .
docker create --name temp-fmu fmu-builder
docker cp temp-fmu:/build/DigitalTwin.fmu ../output/
docker rm temp-fmu
```

### Test the FMU

```bash
cd tests
python test_fmu.py
```

## 📊 What Gets Built

**Input:** `src/BiomassBoiler.mo` (19 KB Modelica source)  
**Output:** `output/DigitalTwin.fmu` (733 KB compiled binary)

The FMU contains:
- Compiled Linux64 binary (`.so`)
- Embedded CVODE solver
- Model metadata (modelDescription.xml)
- 13 input parameters (feeders, air flows, fuel properties)
- 30+ output variables (power, efficiency, emissions, mill data)

## 🔧 Technical Details

- **Compiler:** OpenModelica 1.24.0
- **FMI Version:** 2.0
- **Type:** Co-Simulation
- **Platform:** Linux64
- **Solver:** CVODE (embedded)
- **Build Time:** ~4 seconds
- **Docker Image:** ~1.5 GB (temporary, discarded after build)

## ✅ Validation

Run `tests/test_fmu.py` to verify:
- FMU loads correctly
- Simulation runs without errors
- Outputs are within expected ranges
- All variables are accessible

## 📖 Learn More

- See `../FMU_DELIVERY_GUIDELINES.md` for client delivery standards
- See `../SOURCE_CODE_WORKFLOW.md` for the complete workflow
