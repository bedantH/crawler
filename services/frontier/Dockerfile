# Use official Python base image
FROM python:3.13-slim AS base

# Set the working directory
WORKDIR /app

# Copy project metadata (for uv)
COPY pyproject.toml uv.lock* ./

# Install uv
RUN pip install uv

# Sync only this package's dependencies
RUN uv sync --package . --no-workspace

# Copy the service source and shared library
COPY src/ ./src/
COPY ../../shared/ ./shared/

# Set Python path to find both service and shared modules
ENV PYTHONPATH=/app/src:/app/shared/src

# Expose app port
EXPOSE 8080

# Default command to run your FastAPI app
CMD ["uv", "run", "-p", ".", "uvicorn", "frontier.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
