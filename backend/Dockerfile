FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (will be overridden by docker-compose for each service)
CMD ["python", "app.py"]