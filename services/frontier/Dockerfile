# Use official Python base image
FROM python:3.13-slim AS base

# Set the working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy project metadata
COPY pyproject.toml uv.lock ./
COPY services/frontier/pyproject.toml ./services/frontier/
COPY services/master/pyproject.toml ./services/master/
COPY services/slave/pyproject.toml ./services/slave/
COPY shared/pyproject.toml ./shared/

# Install only third-party deps first (no source needed yet — better layer caching)
RUN uv sync --package frontier --no-dev --no-install-workspace

# Copy the service source and shared library
COPY services/frontier/src/ ./services/frontier/src/
COPY services/frontier/README.md ./services/frontier/
COPY shared/src/ ./shared/src/
COPY shared/README.md ./shared/

# Now install the project itself with source available
RUN uv sync --package frontier --no-dev --no-editable

# Set Python path to find both service and shared modules
ENV PYTHONPATH=/app/services/frontier/src:/app/shared/src

# Expose app port
EXPOSE 8080

# Default command to run your FastAPI app
CMD ["uv", "run", "--package", "frontier", "uvicorn", "frontier.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
