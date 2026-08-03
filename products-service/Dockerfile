FROM python:3.13-slim

# Отключаем буферизацию вывода Python (чтобы логи сразу попадали в docker logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Команда запуска (порт меняется для каждого сервиса: 8001, 8002, 8003, 8004)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
