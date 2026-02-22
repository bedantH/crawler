# Use official Python base image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy project metadata
COPY pyproject.toml uv.lock ./
COPY services/master/pyproject.toml ./services/master/
COPY services/frontier/pyproject.toml ./services/frontier/
COPY services/slave/pyproject.toml ./services/slave/
COPY shared/pyproject.toml ./shared/

# Install only third-party deps first (no source needed yet — better layer caching)
RUN uv sync --package master --no-dev --no-install-workspace

# Copy the service source and shared library
COPY services/master/src/ ./services/master/src/
COPY services/master/README.md ./services/master/
COPY shared/src/ ./shared/src/
COPY shared/README.md ./shared/

# Now install the project itself with source available
RUN uv sync --package master --no-dev --no-editable

# Set Python path to find both service and shared modules
ENV PYTHONPATH=/app/services/master/src:/app/shared/src

# Default command to run your master app
CMD ["uv", "run", "--package", "master", "python", "-m", "master.main"]

