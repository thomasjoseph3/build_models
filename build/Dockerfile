# Multi-stage Dockerfile: Build FMU + Validate in one container
# Supports: .mo files, package directories, data files (.txt, .csv, .mat)
FROM openmodelica/openmodelica:v1.24.0-minimal

# Stage 1: Build FMU
WORKDIR /build

# Copy build script
COPY build/build.mos .

# Copy ALL files from the active model's src/
# This handles:
# - Single .mo files
# - Package directories (package.mo, SubModel.mo, package.order)
# - Data files (.txt, .csv, .mat for CombiTimeTable, etc.)
# Preserves directory structure:
# input/_active/src/model/      -> /build/input/src/model/
# input/_active/src/libraries/  -> /build/input/src/libraries/
# input/_active/src/data/       -> /build/input/src/data/
COPY input/_active/src/ input/src/

# Compile FMU
RUN omc build.mos > build_output.log 2>&1 || true
RUN cat build_output.log

# Verify FMU was created
RUN ls -lh *.fmu || (echo "ERROR: FMU not created!" && exit 1)

# Stage 2: Install Python for validation
# Validation (Conditional)
COPY input/_active/project.yaml .
# Removed generic validate_fmu_docker.py
# COPY tests/validate_fmu_docker.py .

# Create test_data directory and copy test files
RUN mkdir -p test_data
COPY input/_active/test_data ./test_data

# Run validation ONLY if test_script.py exists
RUN if [ -f test_data/test_script.py ]; then \
    echo "Test script found - Installing dependencies..." && \
    apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/* && \
    pip3 install "numpy<2" fmpy pyyaml && \
    echo "Running custom validation script..." && \
    python3 test_data/test_script.py || exit 1; \
    else \
    echo "No custom test script found - skipping validation"; \
    fi

# Final check
RUN echo "Build and validation complete!" && ls -lh *.fmu
