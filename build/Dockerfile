FROM python:3

WORKDIR /app
COPY src /app
RUN pip install -r requirements.txt

ENV PYTHONPATH /app

CMD ["python3", "/app/Collectors/EdgeOS/Collector.py"]
