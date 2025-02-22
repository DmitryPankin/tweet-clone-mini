# Используем официальный образ Python в качестве базового
FROM python:3.12-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Копируем все содержимое директории app в рабочую директорию контейнера
COPY ./app /app

# Копируем папку dist для сервировки статических файлов
COPY ./dist /app/dist

# Экспонируем порт
EXPOSE 8000

# Команда для запуска приложения
CMD ["sh", "-c", "python3 /app/init_db.py && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
