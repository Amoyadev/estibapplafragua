# Estibapp — Guía de inicio para ejecutar

Esta es la referencia rápida para **levantar la aplicación**, **cargar datos de
prueba** y **saber qué hace cada módulo**. Guárdala como punto de partida cuando
comience la migración / despliegue.

---

## 1. Requisitos

- **Docker Desktop** instalado y **en ejecución** (el ícono de la ballena activo).
- Puerto **80** libre en la máquina (lo usa Nginx).
- Archivo **`.env`** en la raíz del proyecto (variables de base de datos y Django).

> No necesitas instalar Python ni PostgreSQL en tu equipo: todo corre dentro de
> contenedores.

---

## 2. ¿Hay un “almacenaje” que encender antes de ejecutar?

**No hay que encender nada manualmente.** El “almacenaje” son los **volúmenes
nombrados de Docker**, que se crean y montan solos cuando levantas los servicios:

| Volumen | Para qué sirve | Persiste al apagar |
|---|---|---|
| `postgres_data` | Base de datos PostgreSQL (clientes, ETAs, etc.) | **Sí** |
| `static_volume` | Archivos estáticos (CSS/JS) que sirve Nginx | Sí |
| `media_volume`  | Archivos subidos por usuarios | Sí |

Lo único que debes “encender” es **Docker Desktop**. Al ejecutar
`docker compose up`, Docker monta automáticamente esos volúmenes y los datos
**se conservan** entre reinicios. Solo se borran si ejecutas explícitamente
`docker compose down -v` (la `-v` elimina los volúmenes).

---

## 3. Levantar la aplicación

Desde la raíz del proyecto (`C:\Users\AlfredoMoya\Documents\APP`):

```powershell
docker compose up --build -d
```

- `--build` reconstruye la imagen de la app (necesario tras cambios de código).
- `-d` la deja corriendo en segundo plano.

Servicios que se levantan:

- `estiba_db`   → PostgreSQL 16
- `estiba_web`  → Django + Gunicorn (no expuesto directamente)
- `estiba_nginx`→ Nginx en el puerto **80**

Abre el navegador en **http://localhost/**

### Aplicar migraciones (solo si cambió el modelo de datos)

```powershell
docker compose exec web python manage.py migrate
```

---

## 4. ¿Qué es `seed_demo`? (datos de prueba)

`seed_demo` es un **comando de gestión de Django** (`manage.py`) que **carga
datos de demostración / QA** para poder ver la app funcionando sin tener que
crear todo a mano:

- **3 usuarios QA** (clave `Estibapp2025*`):
  - `QA_Administrador` — rol Administrador (además entra al admin de Django).
  - `QA_Coordinador` — rol Coordinador.
  - `QA_Patio` — rol Encargado de Patio.
- **Catálogos**: empresas de transporte, agentes portuarios, clientes,
  conductores (cada uno asociado a una empresa), camiones y contenedores.
- **12 ETAs** en distintos estados del ciclo, con sus movimientos y, cuando
  están en depósito, una ubicación física asignada.

> Todo lo que diga “QA”, “Demo” o “de demostración” son **datos de prueba**, no
> reales. Es idempotente: puedes ejecutarlo varias veces sin duplicar catálogos.

Cargar datos:

```powershell
docker compose exec web python manage.py seed_demo
```

Reiniciar SOLO las ETAs/movimientos y volver a generarlas:

```powershell
docker compose exec web python manage.py seed_demo --reset
```

---

## 5. Comandos útiles del día a día

| Acción | Comando |
|---|---|
| Levantar (sin reconstruir) | `docker compose up -d` |
| Levantar reconstruyendo | `docker compose up --build -d` |
| **Apagar sin perder datos** | `docker compose down` |
| Apagar y BORRAR datos | `docker compose down -v` |
| Ver logs de la app | `docker compose logs -f web` |
| Reiniciar solo la app | `docker compose restart web` |
| Validar el proyecto | `docker compose exec web python manage.py check` |
| Crear migraciones | `docker compose exec web python manage.py makemigrations` |
| Aplicar migraciones | `docker compose exec web python manage.py migrate` |
| Recargar datos demo | `docker compose exec web python manage.py seed_demo --reset` |

---

## 6. ¿Qué es cada módulo?

Acceso por rol (un usuario solo ve lo que le corresponde):

| Módulo | Ruta | Qué hace | Roles |
|---|---|---|---|
| **Dashboard** | `/app/` | Vista central de resumen: totales de ETAs, abiertas y en depósito; accesos rápidos. | Todos |
| **ETAs (listado)** | `/app/etas/` | Listado/buscador de todas las ETAs con filtros por estado y texto. Crear y editar solicitudes. | Admin / Coordinador |
| **Detalle de ETA** | `/app/etas/<id>/` | Ficha completa: datos de la solicitud, **estado del ciclo tipo ticket Jira** (botón desplegable para mover el estado), ubicación en patio, registro de movimientos y trazabilidad. | Todos (acciones según rol) |
| **Bandeja** | `/app/bandeja/` | Cola del Coordinador: solicitudes en estado *Solicitado por cliente* / *Asignado* por gestionar. | Admin / Coordinador |
| **Patio** | `/app/patio/` | Tablero **centrado en el contenedor**: tarjetas con código, tipo, carga y **ubicación física**. El jefe de patio registra la ubicación cuando el gruero la indica por radio. | Admin / Encargado de Patio |
| **Recuentos** | `/app/recuentos/` | Conteos **por cliente** (en puerto / en depósito) más las **últimas ETAs** y los **últimos contenedores en puerto y en depósito**. | Admin / Coordinador |
| **Reportes** | `/app/reportes/` | Exportación de información operativa (CSV). | Admin / Coordinador |
| **Catálogos** | `/app/clientes/`, `/app/empresas/`, `/app/conductores/`, `/app/camiones/`, `/app/agentes/`, `/app/contenedores/` | Mantenedores (listas desplegables) de datos maestros. **Empresas** alimenta tanto al conductor (Nombre – Empresa) como a la empresa responsable de cada movimiento. | Admin / Coordinador |
| **Admin Django** | `/admin/` | Panel técnico de administración (solo `QA_Administrador`). | Admin |

### Flujo del ciclo de una ETA

`Solicitado por cliente` → `Asignado` → `En patio` → `Almacenado` →
`Despachado a cliente` → *(retorno)* `Almacenado` → `Despachado a puerto`.

El ciclo traza **dónde está físicamente el contenedor**. No hay estado
«Cerrado»: hay dos cierres según a dónde sale del depósito — **Despachado a
cliente** (cierre parcial: vuelve tras la descarga) y **Despachado a puerto**
(cierre final: fin del ciclo).

El estado inicial **Solicitado por cliente** se muestra como **alerta** en el
detalle para indicar que el proceso aún no comienza.

---

## 7. Acceso

- App: **http://localhost/** → login en **/login/**.
- Usuarios de prueba (clave `Estibapp2025*`): `QA_Administrador`,
  `QA_Coordinador`, `QA_Patio`.
- Sin iniciar sesión **no se ve nada del interior** (el menú y las pantallas
  están protegidos y redirigen al login).
