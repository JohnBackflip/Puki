FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on (adjust if necessary)
EXPOSE 5003

# (optional)
ENV FLASK_APP=main.py

CMD ["python", "main.py"]
