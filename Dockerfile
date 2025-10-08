# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application source code into the container
# This copies everything from the local directory (where the Dockerfile is)
# into the /app directory inside the container.
COPY . .

# Expose the port that Gunicorn will listen on
EXPOSE 8000

# Command to run the application with Gunicorn
# The module is 'app.app' and the app instance is named 'app'.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "5", "--access-logfile", "-", "app:create_app()"]