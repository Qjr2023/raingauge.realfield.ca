# Virtual Rain Gauge API: reads the rain rasters mounted at /data/rain (read-only).
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 RAIN_DIR=/data/rain
# The rasterio wheel bundles GDAL but loads the system libexpat, which the slim image lacks.
RUN apt-get update -q && apt-get install -y -q --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY requirements.txt .
RUN pip install -q -r requirements.txt
COPY app ./app
RUN useradd --system --uid 10001 --no-create-home api
USER api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
