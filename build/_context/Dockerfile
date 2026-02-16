# Multi-stage Dockerfile: Build FMU + Validate in one container
# Supports: .mo files, package directories, data files (.txt, .csv, .mat)
# Base OpenModelica Image (Dynamic Version)
ARG BASE_IMAGE=openmodelica/openmodelica:v1.24.0-minimal
FROM ${BASE_IMAGE}

# Stage 1: Build FMU
WORKDIR /build

# Copy build script (now directly in context root)
COPY build.mos .

# Copy Source Code
# Context structure: input/src/ -> /build/input/src/
COPY input/src/ input/src/

# Compile FMU
RUN omc build.mos > build_output.log 2>&1 || true
RUN cat build_output.log

# Verify FMU was created
RUN ls -lh *.fmu || (echo "ERROR: FMU not created!" && exit 1)

# Stage 2: Install Python for validation
# Validation (Conditional)

# Copy test data and validation scripts
# Context structure: test_data/ -> /build/test_data/
COPY test_data/ test_data/
COPY default_validator.py .
COPY project.yaml .

# Install Python dependencies for validation
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/* && \
    pip3 install "numpy<2" fmpy pyyaml

# Validation Step
# If test_script.py exists in test_data, run it. Else, run default_validator.py
RUN if [ -f test_data/test_script.py ]; then \
    echo "Running custom validation script..." && \
    python3 test_data/test_script.py || exit 1; \
    else \
    echo "No custom test script found - running default validation script..." && \
    python3 default_validator.py || exit 1; \
    fi

# Final check
RUN echo "Build and validation complete!" && ls -lh *.fmu
