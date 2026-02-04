# Multi-stage Dockerfile: Build FMU + Validate in one container
# Supports: .mo files, package directories, data files (.txt, .csv, .mat)
FROM openmodelica/openmodelica:v1.24.0-minimal

# Stage 1: Build FMU
WORKDIR /build

# Copy build script
COPY build/build.mos .

# Copy ALL files from input/src/ (preserves directory structure and data files)
# This handles:
# - Single .mo files
# - Package directories (package.mo, SubModel.mo, package.order)
# - Data files (.txt, .csv, .mat for CombiTimeTable, etc.)
COPY input/src/ .

# Compile FMU
RUN omc build.mos > build_output.log 2>&1 || true
RUN cat build_output.log

# Verify FMU was created
RUN ls -lh *.fmu || (echo "ERROR: FMU not created!" && exit 1)

# Stage 2: Install Python for validation
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install fmpy pyyaml

# Copy project config and validation script
COPY input/project.yaml .
COPY tests/validate_fmu_docker.py .

# Create test_data directory and copy test files
# Note: This will succeed silently if no test_data directory exists
RUN mkdir -p test_data
COPY input/test_data ./test_data

# Stage 3: Run validation (if test data exists)
RUN if [ -f test_data/test_inputs.csv ]; then \
    echo "Running validation tests..." && \
    python3 validate_fmu_docker.py || exit 1; \
    else \
    echo "No test data found - skipping validation"; \
    fi

# Final check
RUN echo "Build and validation complete!" && ls -lh *.fmu
