FROM python:3.10-slim

# تثبيت جافا وأدوات التوقيع والمحاذاة
RUN apt-get update && apt-get install -y \
    default-jdk \
    apksigner \
    zipalign \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# تثبيت الحزم المطلوبة
RUN pip install --no-cache-dir flask pyTelegramBotAPI

# تشغيل السكربت مباشرة عبر بايثون لتفادي مشاكل Gunicorn مع الخيوط الخلفية
CMD python app.py

