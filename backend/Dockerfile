FROM python:3.10-slim

WORKDIR /app

# EVITA EL BUFFER DE LOGS
ENV PYTHONUNBUFFERED 1

# INSTALACION DE DEPENDENCIAS DEL SISTEMA (CRÍTICO PARA GEODJANGO)
# - netcat-openbsd: Para que funcione el entrypoint.sh (nc)
# - gdal-bin, libgdal-dev: Para que funcione GeoDjango y PostGIS
# - python3-gdal, binutils: Librerías auxiliares de mapas
# - libpq-dev, gcc: Para compilar psycopg2
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    binutils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# DAR PERMISOS DE EJECUCIÓN AL ENTRYPOINT
# Esto arregla problemas de permisos si alguien usa Windows
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# El comando final se define en el entrypoint, pero dejamos este por estandar
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]