FROM python:3.9-slim
WORKDIR /usr/src/app
COPY http.reqs.txt amqp.reqs.txt ./
RUN pip install --no-cache-dir -r http.reqs.txt -r amqp.reqs.txt telesign
COPY ./invokes.py ./notification.py ./
CMD ["python", "notification.py"]

