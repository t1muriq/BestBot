FROM python:3.10-slim

WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все необходимые файлы проекта
COPY bot.py models.py migrations.py /app/

# Создаем директорию для логов
RUN mkdir -p /app/logs

CMD ["python", "bot.py"]
