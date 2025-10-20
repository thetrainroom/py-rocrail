# Rocrail Docker Image for Testing PyRocrail
# Multi-stage build: Copy Rocrail from evili/rocrail into Python 3.12 base

# Stage 1: Get Rocrail from evili/rocrail
FROM evili/rocrail:latest AS rocrail-base

# Stage 2: Build final image with Python 3.12
FROM python:3.12-slim

# Install Rocrail dependencies
RUN apt-get update && apt-get install -y \
    libgtk2.0-0 \
    libglib2.0-0 \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Copy Rocrail binaries from first stage
COPY --from=rocrail-base /opt/rocrail /opt/rocrail
COPY --from=rocrail-base /entrypoint.sh /entrypoint.sh

# Set working directory
WORKDIR /rocrail

# Copy demo plan files to working directory
COPY example_plan/plan.xml example_plan/rocrail.ini example_plan/occ.xml ./

# Copy PyRocrail source code and project files for installation
COPY src/ /pyrocrail/src/
COPY pyproject.toml README.md /pyrocrail/

# Create directory for test scripts
RUN mkdir -p /tests

# Check Python version
RUN python3 --version

# Install PyRocrail in editable mode (mounted source will override at runtime)
RUN cd /pyrocrail && pip install -e .

# Expose Rocrail control port
EXPOSE 8051

# Use the entrypoint from evili/rocrail
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/entrypoint.sh"]
