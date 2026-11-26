# Virtual Rain Gauge API: reads the rain rasters mounted at /data/rain (read-only).
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 RAIN_DIR=/data/rain
WORKDIR /srv
COPY requirements.txt .
RUN pip install -q -r requirements.txt
COPY app ./app
RUN useradd --system --uid 10001 --no-create-home api
USER api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
