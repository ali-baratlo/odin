#!/bin/sh



#echo "==== ENV VARIABLES ===="
#env | grep DB
#echo "========================"

echo "Waiting for PostgreSQL to be ready..."

until pg_isready -h "$DB_HOST" -p "$DB_SERVICE_PORT" -U "$DB_USER"; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up and running!"

echo "Running database initialization script..."
export PGPASSWORD="$DB_PASSWORD"
psql -h "$DB_HOST" -p "$DB_SERVICE_PORT" -U "$DB_USER" -d "$DB_NAME" -f /app/init.sql

if [ $? -ne 0 ]; then
  echo "Error: Database initialization failed."
  exit 1
fi

echo "Database initialization complete."

echo "Starting application..."
exec "$@"