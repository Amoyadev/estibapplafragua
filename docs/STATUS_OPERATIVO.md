# Estado Operativo — Estibapp

> Última actualización: 12 de junio de 2026

## Stack levantado (ambiente dev)

| Servicio | Contenedor | Imagen | Estado | Puertos |
|----------|-----------|--------|--------|---------|
| Base de datos | `estiba_db` | `postgres:16-alpine` | Up — healthy | 5432 (interno) |
| Web (Django) | `estiba_web` | `app-web` | Up — `runserver` | 8000 (interno) |
| Reverse proxy | `estiba_nginx` | `nginx:1.27-alpine` | Up | `0.0.0.0:80->80` |

- Settings activos: `config.settings.dev` (`DEBUG=True`).
- Override de desarrollo activo (`docker-compose.override.yml`): bind-mount del código + `runserver`, sin reconstruir imagen por cada cambio.

## Verificaciones realizadas

- [x] `python.analysis.typeCheckingMode: "basic"` en `.vscode/settings.json`.
- [x] Migración `auditoria.0001_initial` aplicada automáticamente al iniciar el contenedor.
- [x] `System check identified no issues (0 silenced)`.
- [x] Seed `seed_demo --reset` ejecutado correctamente.
- [x] HTTP a `http://localhost/` → **200 OK** (cadena nginx → web operativa).

## Datos de demostración cargados

- 12 ETAs base + movimientos con fechas escalonadas (para gráficos temporales).
- **Tattersall** como cliente principal: **4 en depósito (~47%)** + **3 devueltos a puerto (estado DESPACHADO_PUERTO)**.
- Catálogos: 5 empresas, 4 agentes, 8 clientes, 8 conductores, 6 camiones, 15 contenedores.

## Accesos

- **App**: `http://localhost/`
- **Gráficos / Reportes**: `http://localhost/app/reportes/`
- **Usuarios QA** (clave: `Estibapp2025*`):
  - `QA_Administrador` (rol Administrador, sin acceso al admin de Django)
  - `QA_Coordinador` (rol Coordinador)
  - `QA_Patio` (rol Encargado de Patio)
- **Admin Django** (`/admin/`, solo dev): requiere superusuario creado manualmente.

## Comandos operativos

```powershell
# Construir imagen (tras cambios en dependencias/Dockerfile)
docker compose build web

# Levantar stack (override de dev se aplica solo)
docker compose up -d

# Estado y logs
docker compose ps
docker compose logs web --tail 40

# Recargar datos demo (Tattersall 47% requiere --reset)
docker compose exec web python manage.py seed_demo --reset

# Crear superusuario para el admin de Django (solo dev)
docker compose exec web python manage.py createsuperuser

# Detener stack
docker compose down
```

## Próximos pasos

- Migración de datos reales desde SharePoint (ver `docs/INFORME_PROYECTO_ESTIBA.md`, sección 12.5).
- Notas de estado para producción en `docs/INFORME_PROYECTO_ESTIBA.md`, sección 12.6.
- Lógica de reportes/gráficos documentada en `docs/REPORTES_Y_GRAFOS.md`.
