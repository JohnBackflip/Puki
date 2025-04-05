FROM python:3.9-slim
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY http.reqs.txt ./
RUN pip install --no-cache-dir -r http.reqs.txt

# Set development environment
ENV FLASK_ENV=development

COPY ./keycard.py ./
CMD ["python", "keycard.py"]

