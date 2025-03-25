# Use an official Python runtime as a parent image
FROM python:3.9-slim

WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the service listens on
EXPOSE 5004

# Run the application
CMD ["python", "main.py"]
