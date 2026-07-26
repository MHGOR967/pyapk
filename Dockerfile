FROM python:3.10-slim

# تثبيت جافا وأدوات التوقيع الرسمية لأندرويد
RUN apt-get update && apt-get install -y \
    default-jdk \
    apksigner \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir flask gunicorn

CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 180

