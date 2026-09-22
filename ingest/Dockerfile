FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY syslog_server.py .

ENV PYTHONUNBUFFERED=1
EXPOSE 514/udp
CMD ["python", "syslog_server.py"]
