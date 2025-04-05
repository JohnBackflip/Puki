FROM python:3.9-slim
WORKDIR /usr/src/app
COPY http.reqs.txt ./
RUN pip install --no-cache-dir -r http.reqs.txt
COPY ./makebooking.py ./invokes.py ./
CMD ["python", "makebooking.py"]
