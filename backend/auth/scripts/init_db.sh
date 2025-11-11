#!/bin/bash
set -e

# Ожидаем пока база данных будет готова
echo "Ожидание пока база данных будет готова..."
until PGPASSWORD="${DB_PASS}" psql -h "${DB_HOST}" -U "${DB_USERNAME}" -c '\q'; do
  echo "PostgreSQL недоступен - ожидание..."
  sleep 1
done

# Удаляем базу, если она существует
echo "Удаление существующей базы..."
PGPASSWORD="${DB_PASS}" psql -h "${DB_HOST}" -U "${DB_USERNAME}" -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";"

# Создаем новую базу
echo "Создание новой базы..."
PGPASSWORD="${DB_PASS}" psql -h "${DB_HOST}" -U "${DB_USERNAME}" -c "CREATE DATABASE \"${DB_NAME}\" WITH ENCODING 'UTF8';"

# Выполняем миграции
echo "Выполнение миграций..."
cd /app
export PYTHONPATH=/app

# Удаляем старые миграции и создаем новые
rm -rf /app/migrations/versions/*
poetry run alembic revision --autogenerate -m 'Initial'
poetry run alembic upgrade head

# Инициализируем роли
echo "Инициализация ролей..."
poetry run python scripts/init_roles.py

echo "Инициализация базы данных завершена!"
exec "$@"