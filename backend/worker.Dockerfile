FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system mindbridge && adduser --system --ingroup mindbridge mindbridge
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R mindbridge:mindbridge /app
USER mindbridge
CMD ["python", "scripts_notification_worker.py"]
