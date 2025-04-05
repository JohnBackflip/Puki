FROM python:3.9-slim
WORKDIR /usr/src/app
COPY http.reqs.txt ./
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r http.reqs.txt
COPY ./roster.py ./invokes.py ./
CMD ["python", "roster.py"]

