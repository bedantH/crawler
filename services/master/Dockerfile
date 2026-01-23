# Use official Python base image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy project metadata
COPY pyproject.toml uv.lock ./
COPY services/master/pyproject.toml ./services/master/
COPY shared/pyproject.toml ./shared/

# Install dependencies for the workspace
RUN uv sync --package master --no-dev --no-editable

# Copy the service source and shared library
COPY services/master/src/ ./services/master/src/
COPY shared/src/ ./shared/src/

# Sync again to ensure everything is in place
RUN uv sync --package master --no-dev --no-editable

# Set Python path to find both service and shared modules
ENV PYTHONPATH=/app/services/master/src:/app/shared/src

# Default command to run your master app
CMD ["uv", "run", "--package", "master", "python", "-m", "master.main"]
