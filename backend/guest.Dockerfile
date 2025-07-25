FROM python:3.9-slim
WORKDIR /usr/src/app
COPY http.reqs.txt ./
RUN pip install --no-cache-dir -r http.reqs.txt
COPY ./guest.py ./
CMD ["python", "guest.py"]

