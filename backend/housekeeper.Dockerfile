FROM python:3.9-slim
WORKDIR /usr/src/app
COPY http.reqs.txt ./
RUN pip install --no-cache-dir -r http.reqs.txt
COPY ./housekeeper.py ./invokes.py ./
CMD ["python", "housekeeper.py"]

