# Rocrail Docker Image for Testing PyRocrail
# Build Rocrail with Python 3.12

FROM python:3.12-slim

# Install Rocrail dependencies and download tools
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libgtk2.0-0 \
    libglib2.0-0 \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Download and install Rocrail from snapshot
ARG ROCRAIL_PACKAGE=Debian/Rocrail-debian11-i64.zip
RUN wget https://wiki.rocrail.net/rocrail-snapshot/${ROCRAIL_PACKAGE} -O /tmp/rocrail.zip \
    && mkdir -p /opt/rocrail \
    && unzip /tmp/rocrail.zip -d /opt/rocrail \
    && chmod +x /opt/rocrail/bin/rocrail \
    && rm /tmp/rocrail.zip

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -euo pipefail\n\
if [[ ! -e svg ]]; then\n\
    ln -svi /opt/rocrail/svg .\n\
fi\n\
/opt/rocrail/bin/rocrail -l /opt/rocrail/bin\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

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
