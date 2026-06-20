# 🛳️ Estiba

Sistema de Gestión de Depósito Portuario de Contenedores (retiro · almacenaje · trazabilidad · despacho).

**Stack:** Django 5 · PostgreSQL 16 · Nginx · Gunicorn · Docker Compose

> 📄 Plan de proyecto completo (formato Notion): [`docs/INFORME_PROYECTO_ESTIBA.md`](docs/INFORME_PROYECTO_ESTIBA.md)

---

## 🚀 Levantar con Docker (recomendado)

Requisitos: Docker Desktop / Docker Engine + Docker Compose.

```bash
# 1. Crear el archivo de entorno a partir del ejemplo
cp .env.example .env        # En Windows PowerShell: Copy-Item .env.example .env

# 2. Editar .env y cambiar SECRET_KEY y POSTGRES_PASSWORD

# 3. Construir y levantar
docker compose up --build
```

La app queda disponible en:

- **App:** http://localhost
- **Admin:** http://localhost/admin
- **Health:** http://localhost/health

### Crear un superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

### Detener / limpiar

```bash
docker compose down            # detiene contenedores
docker compose down -v         # detiene y borra volúmenes (datos BD)
```

---

## 🧩 Estructura del proyecto

```
APP/
├─ config/                  # Proyecto Django (settings, urls, wsgi/asgi)
│  └─ settings/             # base.py · dev.py · prod.py
├─ apps/
│  ├─ core/                 # Home, health check, comando wait_for_db
│  └─ operaciones/          # Modelos del dominio (ETA, Contenedor, etc.)
├─ nginx/                   # Reverse proxy
├─ docs/                    # Informe de proyecto (Notion)
├─ Dockerfile
├─ docker-compose.yml
├─ entrypoint.sh
├─ requirements.txt
└─ .env.example
```

---

## 💻 Desarrollo local sin Docker (opcional)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Necesitas un PostgreSQL local y un .env apuntando a él (POSTGRES_HOST=localhost)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🔐 Buenas prácticas incluidas

- Contenedor con **usuario no-root**.
- Secretos por **variables de entorno** (`.env`, nunca en el repo).
- Settings separados **dev / prod**.
- **Health check** de BD (`wait_for_db`) antes de migrar.
- Estáticos servidos por **Nginx** + WhiteNoise como respaldo.
- `.dockerignore` / `.gitignore` para imágenes limpias.

---

## 📦 Portabilidad a otro equipo

El proyecto es autocontenido: basta copiar la carpeta (sin `.env`), crear el `.env`
en el equipo destino y ejecutar `docker compose up --build`. Ideal para probar
infraestructura (Nginx) y demostrar operatividad al cliente.
