FROM python:3.11-slim

WORKDIR /app

# تثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY bot.py .
COPY server.py .
COPY add_images.py .

# إنشاء المجلدات
RUN mkdir -p images

# تعيين المتغيرات البيئية
ENV DATABASE_PATH=images.db
ENV IMAGES_FOLDER=images
ENV PORT=10000

# كشف المنفذ
EXPOSE 10000

# تشغيل الخادم
CMD ["python", "server.py"]
