#!/bin/bash
set -e

echo "Инициализация ключей для JWT..."

# Создаем директорию, если её нет
mkdir -p /app/certs 2>/dev/null || true

# Проверяем наличие хотя бы одного ключа
if [ -f "/app/certs/jwt-private.pem" ] || [ -f "/app/certs/jwt-public.pem" ]; then
    echo "Обнаружены существующие ключи. Удаление..."
    rm -f /app/certs/jwt-*.pem 2>/dev/null || true
fi

# Генерируем новые ключи для JWT
echo "Генерация новых ключей..."
openssl genrsa -out /app/certs/jwt-private.pem 2048
openssl rsa -in /app/certs/jwt-private.pem -pubout -out /app/certs/jwt-public.pem

# Устанавливаем правильные права на файлы
# chmod 644 /app/certs/*.pem

echo "Инициализация ключей для JWT завершена!"
exec "$@"