# ⚙️ operativa.md — Datos de prueba y operación diaria (Estibapp)

> Documento de **operación QA / demo**. Reúne, ordenado para archivar aparte, los
> accesos genéricos, los usuarios de prueba y un flujo operativo diario para validar
> la app siguiendo el [Manual de Usuario](MANUAL_USUARIO_ESTIBAPP.md).
>
> ⚠️ **Datos genéricos / no productivos.** Cambiar todas las contraseñas antes de
> cualquier ambiente real.

---

## 1. Cómo dejar la app lista (cargar datos de prueba)

Los datos de prueba se generan con un comando de carga (**seed**), que crea los
usuarios QA, los catálogos y ETAs de ejemplo. Es **idempotente** (se puede repetir).

### Con Docker (recomendado)
```powershell
cd C:\Users\AlfredoMoya\Documents\APP
docker compose up --build -d
docker compose exec web python manage.py seed_demo
```

### Sin Docker (entorno local de desarrollo)
```powershell
cd C:\Users\AlfredoMoya\Documents\APP
$env:PYTHONPATH=""
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

Opciones del comando:
```powershell
python manage.py seed_demo                      # carga estándar (12 ETAs)
python manage.py seed_demo --reset              # borra ETAs/movimientos y regenera
python manage.py seed_demo --etas 30            # genera 30 ETAs
python manage.py seed_demo --password "Otra123*"  # define otra clave QA
```

---

## 2. Accesos (datos genéricos)

| Recurso | URL (local) | URL (servidor) |
|---------|-------------|----------------|
| App (login) | http://localhost/login/ | https://<dominio>/login/ |
| App (dashboard) | http://localhost/app/ | https://<dominio>/app/ |
| **Admin Django** | http://localhost/admin/ | https://<dominio>/admin/ |

> Con Docker el puerto público es el **80** (`http://localhost/...`).
> Con `runserver` sin Docker es el **8000** (`http://localhost:8000/...`).

### Superusuario para el Admin Django
El usuario **QA_Administrador** se crea como **superusuario** (acceso total al admin):

| Campo | Valor genérico |
|-------|----------------|
| Usuario | `QA_Administrador` |
| Contraseña | `Estibapp2025*` |
| URL admin | http://localhost/admin/ |

> Si prefieres un superusuario propio adicional:
> ```powershell
> docker compose exec web python manage.py createsuperuser
> ```

---

## 3. Usuarios QA por rol (datos genéricos)

Todos comparten la misma contraseña por defecto: **`Estibapp2025*`**

| Usuario | Rol (grupo) | Contraseña | Accede a Admin Django | Para probar |
|---------|-------------|------------|------------------------|-------------|
| `QA_Administrador` | Administrador | `Estibapp2025*` | ✅ Sí (superusuario) | Todo: catálogos, ETAs, bandeja, patio, recuentos, reportes, admin. |
| `QA_Coordinador` | Coordinador | `Estibapp2025*` | ❌ No | Crear/editar catálogos y ETAs, bandeja, avanzar ciclo, reportes. |
| `QA_Patio` | Encargado de Patio | `Estibapp2025*` | ❌ No | Ver catálogos, tablero de patio, avanzar ETAs, movimientos, reportes. |

> Estos usuarios se mapean 1:1 con los roles descritos en el Manual de Usuario,
> sección 2, para revisar cada pantalla con el perfil correcto.

---

## 4. Datos base generados (resumen)

El seed crea automáticamente (valores aleatorios genéricos):

| Catálogo | Cantidad | Ejemplos |
|----------|----------|----------|
| Agentes portuarios | 4 | TPS, PCE, STI, TCVAL |
| Clientes | 8 | Comercial Andes, Frutícola del Maipo, … |
| Conductores | 8 | Juan Pérez, Marco Rojas, … |
| Camiones | 6 | patentes tipo `BCDF45` |
| Contenedores | 15 | códigos tipo `ABCD1234567` |
| ETAs | 12 | `ETA-2026-0001` … en estados variados |

Las ETAs nacen en distintos puntos del ciclo, con sus **movimientos**
correspondientes ya registrados (para ver trazabilidad sin cargar todo a mano).

---

## 5. Flujo operativo diario — prueba en 7 pasos

Guion corto para validar un día típico de operación. Hazlo de punta a punta.

1. **Login Coordinador** — entra con `QA_Coordinador` en http://localhost/login/.
   Verifica que el dashboard muestra totales y ETAs recientes.

2. **Crear solicitud (ETA)** — menú **ETAs → Nueva ETA**. Completa N° ETA, cliente,
   agente, contenedor, depósito y fecha. Guarda → debe quedar en estado **Solicitado**.

3. **Asignar transporte** — en la ficha de la ETA, **Editar datos** y asigna
   **conductor** y **camión**. Avanza con **Avanzar a «Asignado»**.

4. **Login Encargado de Patio** — cierra sesión y entra con `QA_Patio`.
   Ve al menú **Patio**: la ETA recién asignada debe aparecer en el tablero.

5. **Recepción y almacenaje** — abre la ETA y presiona **Avanzar** dos veces:
   `Asignado → En patio` (genera **Retiro**) y `En patio → Almacenado`
   (genera **Almacenaje**). Revisa la tabla de **Trazabilidad**.

6. **Despacho y cierre** — sigue avanzando: `Almacenado → Despachado a cliente`
   (genera **Despacho a cliente**, cierre parcial), luego el retorno
   `Despachado a cliente → Almacenado` (genera **Retorno**) y finalmente
   `Almacenado → Despachado a puerto` (genera **Despacho a puerto**, cierre
   final). El botón Avanzar desaparece: ciclo completo.

7. **Reportes y recuentos** — entra con `QA_Administrador`. En **Recuentos**
   revisa puerto vs depósito; en **Reportes** descarga los CSV de
   *retiro / almacenados / entregas* y ábrelos en Excel.

> ✅ Si los 7 pasos funcionan, el MVP 1 cumple las condiciones de aceptación
> CA-1 a CA-8 del informe.

---

## 6. Reinicio de datos de prueba

Para volver a un estado limpio de ETAs sin perder los catálogos:
```powershell
docker compose exec web python manage.py seed_demo --reset
```

Para borrar TODO (incluida la base de datos) y empezar de cero:
```powershell
docker compose down -v
docker compose up --build -d
docker compose exec web python manage.py seed_demo
```

---

## 7. Checklist rápido de validación

- [ ] `seed_demo` corre sin errores y reporta usuarios + catálogos + ETAs.
- [ ] `QA_Administrador` entra al admin Django (`/admin/`).
- [ ] Cada usuario QA ve solo su menú según rol.
- [ ] El flujo de 7 pasos completa una ETA de Solicitado a Cerrado.
- [ ] Cada avance deja su movimiento en Trazabilidad.
- [ ] Los 3 CSV de reportes abren correctamente en Excel.

---

### 🔐 Recordatorio de seguridad
Las contraseñas de este documento son **genéricas para QA/demo**. En cualquier
ambiente real: cambiar `Estibapp2025*`, no reutilizar el superusuario de demo y
activar las medidas de la Fase 2 (HTTPS, 2FA, backups).
