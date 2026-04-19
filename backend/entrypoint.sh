#!/bin/sh

# Esperar a que Postgres esté listo (loop simple)
echo "Esperando a la base de datos..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Base de datos iniciada"

# Correr migraciones automáticamente
echo "Aplicando migraciones..."
python manage.py migrate

# (Opcional) Cargar datos iniciales si existen
# python manage.py loaddata fixtures/initial_data.json

# Arrancar el servidor
echo "Iniciando servidor..."
exec "$@"