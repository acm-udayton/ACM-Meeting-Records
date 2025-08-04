# Base Python image.
FROM python:3.9-slim-buster

WORKDIR app

# Copy and install required dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code.
COPY . .

# Expose the flask application port.
EXPOSE 5000

# Command to run the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]