FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=120

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r /app/requirements.txt

COPY . /app

EXPOSE 8002

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]