FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV JOBHUNT_DB_PATH=/app/data/jobhunt.db

WORKDIR /app

COPY requirements.txt requirements-api.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements-api.txt

COPY . .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 CMD ["python", "healthcheck.py"]

CMD ["python", "main.py"]
