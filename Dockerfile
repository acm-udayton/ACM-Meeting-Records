# Use an official Python runtime as a parent image.
FROM python:3.11-slim

# Install uv from the official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvbin/uv
ENV PATH="/uvbin:$PATH"

# Set the working directory in the container.
WORKDIR /app

# Copy lockfile and pyproject.toml first to cache dependencies.
COPY pyproject.toml uv.lock ./

# Install the Python dependencies using uv.
RUN uv sync --frozen --no-dev --no-install-project


# Copy the entire application source code into the container.
# This copies everything from the local directory (where the Dockerfile is)
# into the /app directory inside the container.
COPY . .

# Install the project itself with uv.
RUN uv sync --frozen --no-dev

# Expose the port that Gunicorn will listen on.
EXPOSE 8000

# Command to run the application with Gunicorn.
# Add the venv to the PATH so commands like 'gunicorn' are found automatically.
ENV PATH="/app/.venv/bin:$PATH"

# The module is 'app.app' and the app instance is named 'app'.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "5", "--access-logfile", "-", "app:create_app()"]