FROM python:3.10-slim

# تثبيت جافا، أداة التوقيع apksigner، وأداة المحاذاة zipalign
RUN apt-get update && apt-get install -y \
    default-jdk \
    apksigner \
    zipalign \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir flask gunicorn pyTelegramBotAPI

# استخدام Gunicorn مع مهلة زمنية 300 ثانية لمنع أخطاء الـ Timeout أثناء إرسال التطبيق
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 300

