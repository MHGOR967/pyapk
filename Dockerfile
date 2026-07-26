FROM python:3.10-slim

# تثبيت جافا، أدوات التوقيع والمحاذاة
RUN apt-get update && apt-get install -y \
    default-jdk \
    apksigner \
    zipalign \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir flask gunicorn pyTelegramBotAPI

CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 180

