# ===== Estiba — Dockerfile (multi-stage) =====
FROM python:3.13-slim AS base

# Buenas prácticas de runtime Python en contenedor
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema (libpq para psycopg, gettext opcional)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias primero (mejor cache de capas)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el código
COPY . .

# Usuario no-root por seguridad
RUN addgroup --system estiba \
    && adduser --system --ingroup estiba estiba \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R estiba:estiba /app

USER estiba

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
