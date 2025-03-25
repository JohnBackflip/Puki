FROM python:3.9-slim

WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Expose the port the service listens on (as defined in main.py)
EXPOSE 5006

# Run the application
CMD ["python", "main.py"]
