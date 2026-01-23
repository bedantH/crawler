# Use official Python base image
FROM python:3.13-slim AS base

# Set the working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy project metadata
COPY pyproject.toml uv.lock ./
COPY services/frontier/pyproject.toml ./services/frontier/
COPY shared/pyproject.toml ./shared/

# Install dependencies for the workspace
# Note: we need to copy enough for uv to resolve workspace members
RUN uv sync --package frontier --no-dev --no-editable

# Copy the service source and shared library
COPY services/frontier/src/ ./services/frontier/src/
COPY shared/src/ ./shared/src/

# Sync again to ensure everything is in place
RUN uv sync --package frontier --no-dev --no-editable

# Set Python path to find both service and shared modules
ENV PYTHONPATH=/app/services/frontier/src:/app/shared/src

# Expose app port
EXPOSE 8080

# Default command to run your FastAPI app
CMD ["uv", "run", "--package", "frontier", "uvicorn", "frontier.main:app", "--host", "0.0.0.0", "--port", "8080"]
