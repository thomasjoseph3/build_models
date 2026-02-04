# Dockerfile for Building FMU from Modelica Source Code
# Standard structure: src/ contains source, output/ contains generated FMU

FROM openmodelica/openmodelica:v1.24.0-minimal

WORKDIR /build

# Copy the Modelica source file and build script
COPY ../src/BiomassBoiler.mo .
COPY build.mos .

# Run the build process and show output
RUN omc build.mos > build_output.log 2>&1 || true

# Show the build log
RUN cat build_output.log

# List the generated files to verify FMU was created
RUN ls -lh

# The FMU will be created as DigitalTwin.fmu in the /build directory
CMD ["sh", "-c", "if [ -f DigitalTwin.fmu ]; then ls -lh DigitalTwin.fmu; else echo 'FMU not generated. Check build_output.log'; cat build_output.log; fi"]
