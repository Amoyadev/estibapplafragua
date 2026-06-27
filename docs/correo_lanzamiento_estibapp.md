# Correos de comunicación — EstibAPP

---

## Correo 1 — Lanzamiento de maqueta (revisión inicial)

**Asunto:** EstibAPP — Maqueta operativa disponible para revisión y feedback

---

Estimado equipo,

Junto con saludar, les informamos que la maqueta principal de **EstibAPP** se encuentra operativa y disponible para su revisión en el siguiente enlace:

🔗 **https://estibapplafragua.cl**

---

### ¿Qué es EstibAPP?

EstibAPP es una plataforma web de gestión operacional para el depósito de contenedores, diseñada para centralizar el seguimiento de retiros, almacenaje y despachos en tiempo real. Permite a cada perfil de usuario acceder únicamente a la información y funciones que le corresponden.

---

### Características principales

- **Gestión de ETAs**: creación y seguimiento del ciclo completo de cada contenedor (solicitud → almacenaje → despacho a cliente → despacho a puerto).
- **Tablero operativo del día**: visión diaria de retiros y despachos programados.
- **Panel de control (Dashboard)**: KPIs y gráficos de actividad por período (semana, mes, trimestre, año).
- **Cronograma Retiro / Despacho**: vista ejecutiva por conductor y patente de camión, con filtro de búsqueda.
- **Patio**: control de ubicación y estado de contenedores en depósito.
- **Recuentos**: resumen por cliente con stock en puerto y en depósito.
- **Reportes**: exportación CSV por período y cliente (perfil Administrador).
- **Mantenedor**: gestión de clientes, conductores, camiones, empresas, agentes y contenedores.

---

### Acceso por perfil

| Perfil | Usuario | Contraseña | Acceso |
|--------|---------|------------|--------|
| Administrador | `Administrador` | `superadmin12345` | Acceso completo + reportes + admin Django |
| Coordinador | `Coordinador` | `admin12345` | Bandeja, ETAs, tablero, recuentos |

---

### Nota importante

La plataforma se encuentra actualmente **en proceso de integración con correo vía IMAP** (conexión con bandeja entrante para recepción automática de solicitudes). Este módulo está en proceso de acoplamiento.

La maqueta principal está **completamente operativa** con datos de prueba desde enero 2025 hasta la fecha, lo que permite explorar todas las funcionalidades y temporalidades.

El objetivo de esta etapa es **recibir feedback** del equipo y realizar ajustes antes del despliegue definitivo.

Saludos cordiales,
**Equipo de desarrollo — EstibAPP**

---

## Correo 2 — Nuevas funcionalidades (post-revisión stakeholder)

**Asunto:** EstibAPP · Nuevas funcionalidades disponibles para revisión

---

Estimado/a,

Gracias por tomarse el tiempo de revisar la aplicación. Hemos incorporado las funcionalidades acordadas y quedaron disponibles en el entorno de prueba.

**Acceso**
🔗 https://estibapplafragua.cl
Usuario: `Coordinador` · Contraseña: `admin12345`

---

**Mantenedor de conductores**
En el menú lateral encontrará la sección *Conductores*. Desde ahí puede ver el listado completo, editar el perfil de cada conductor y, en la parte inferior de cada ficha, registrar sus **días libres** (vacaciones, permisos, ausencias). Esto es importante porque el sistema los considera al momento de asignar transporte: un conductor con día libre en la fecha de operación aparece marcado como *no disponible* en el formulario de ETA.

**Ciclo de ETA desde la bandeja**
Al ingresar a cualquier ETA desde la bandeja del coordinador, encontrará el panel *Ciclo del contenedor* a la derecha. Desde ahí se gestiona todo el avance de la operación:

- **Asignación de conductor:** el formulario muestra los conductores separados en dos grupos — *Disponibles* y *No disponibles ese día* — en base al mantenedor de días libres. Se recomienda seleccionar siempre del grupo disponible.

- **Avance de estados:** el contenedor recorre un ciclo definido. Dependiendo del estado actual, el formulario habilita solo las transiciones válidas. En los estados que implican movimiento de camión (*Despachado a cliente*, *Despachado a puerto*) el sistema solicita asignar camión y conductor; en los estados de almacenaje, no. Esto evita registros incompletos y mantiene la trazabilidad limpia.

Cada movimiento queda registrado en la tabla de trazabilidad al pie de la página, con fecha, empresa responsable y observación.

---

Quedo atento a cualquier consulta o ajuste que surja de la revisión.

Saludos,
**Equipo de desarrollo — EstibAPP**
