# Correo de lanzamiento — EstibAPP

---

**Asunto:** EstibAPP — Maqueta operativa disponible para revisión y feedback

---

**Cuerpo:**

Estimado equipo,

Junto con saludar, les informamos que la maqueta principal de **EstibAPP** se encuentra operativa y disponible para su revisión en el siguiente enlace:

🔗 **https://estibapplafragua.cl**

---

## ¿Qué es EstibAPP?

EstibAPP es una plataforma web de gestión operacional para el depósito de contenedores, diseñada para centralizar el seguimiento de retiros, almacenaje y despachos en tiempo real. Permite a cada perfil de usuario acceder únicamente a la información y funciones que le corresponden.

---

## Características principales

- **Gestión de ETAs**: creación y seguimiento del ciclo completo de cada contenedor (solicitud → retiro → almacenaje → despacho a cliente → despacho a puerto).
- **Tablero operativo del día**: visión diaria de retiros y despachos programados.
- **Panel de control (Dashboard)**: KPIs y gráficos de actividad por período (semana, mes, trimestre, año).
- **Cronograma Retiro / Despacho**: vista ejecutiva con cronograma por conductor y patente de camión, con filtro de búsqueda.
- **Patio**: control de ubicación y estado de contenedores en depósito.
- **Recuentos**: resumen por cliente con stock en puerto y en depósito.
- **Reportes**: exportación CSV por período y cliente (perfil Administrador).
- **Mantenedor**: gestión de clientes, conductores, camiones, empresas, agentes y contenedores.

---

## Acceso por perfil

| Perfil | Usuario | Contraseña | Acceso |
|--------|---------|------------|--------|
| Administrador | `Administrador` | `superadmin12345` | Acceso completo + reportes + admin Django |
| Coordinador | `Coordinador` | `admin12345` | Bandeja, ETAs, tablero, recuentos (sin patio ni reportes) |

---

## Nota importante

La plataforma se encuentra actualmente **en proceso de integración con correo vía IMAP** (conexión con bandeja entrante para recepción automática de solicitudes). Este módulo está en conocimiento del equipo técnico y en proceso de acoplamiento.

La maqueta principal, sin embargo, está **completamente operativa** con datos de prueba desde enero 2025 hasta la fecha, lo que permite explorar todas las funcionalidades y temporalidades (semana, mes, trimestre, año).

El objetivo de esta etapa es **recibir feedback** del equipo y realizar ajustes antes del despliegue definitivo.

Cualquier observación, mejora o corrección puede enviarse directamente a respuesta a este correo.

Saludos cordiales,

**Equipo de desarrollo — EstibAPP**
