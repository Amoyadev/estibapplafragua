# Manual de Usuario — EstibAPP

> Plataforma de gestión de depósito portuario de contenedores.
> Versión de producción: **v1.0-estable** · Rama activa de desarrollo: `develop`
> URL: https://estibapplafragua.cl

---

## 1. ¿Qué hace EstibAPP?

EstibAPP registra y da trazabilidad al ciclo de un contenedor desde que el cliente lo solicita hasta que se cierra la operación. El documento central es la **ETA**, que conecta cliente, agente portuario, contenedor, conductor y camión, y avanza por una serie de **estados**.

**Ciclo de una ETA:**

```
Solicitado → Asignado → Almacenado → Despachado a cliente → (retorno) Almacenado → Despachado a puerto
```

> El sistema atraviesa automáticamente el estado intermedio *En patio* al registrar el almacenaje; no aparece como opción en el formulario.

El ciclo sigue **dónde está físicamente el contenedor**. Hay dos cierres:

- **Despachado a cliente** (cierre parcial): el contenedor se entrega al cliente y **vuelve** al depósito tras la descarga (regresa a *Almacenado*).
- **Despachado a puerto** (cierre final): el contenedor se devuelve al puerto; el ciclo termina.

Cada vez que la ETA entra a un estado operativo se registra un **movimiento** (almacenaje, despacho a cliente, retorno, despacho a puerto) en la tabla de trazabilidad.

---

## 2. Roles y accesos

| Rol | Para qué sirve | Accesos |
|-----|----------------|---------|
| **Administrador** | Configura todo y supervisa. | Todo: catálogos, ETAs, bandeja, patio, recuentos, reportes, admin Django. |
| **Coordinador** | Crea y gestiona solicitudes. | Catálogos (crear/editar), crear y avanzar ETAs, bandeja, recuentos, reportes. |
| **Encargado de Patio** | Mueve contenedores físicamente. | Ver catálogos, ver y avanzar ETAs en patio, recuentos, reportes. |

> Los roles se asignan desde el **Admin de Django** (`/admin/`) agregando el usuario al grupo correspondiente.

---

## 3. Ingreso al sistema

1. Abre https://estibapplafragua.cl/login/
2. Ingresa tu **usuario** y **contraseña**.
3. Llegarás al **Dashboard** con KPIs, gráficos de actividad y acciones rápidas según tu rol.
4. Para salir usa el botón **Salir** (menú lateral, parte inferior).

---

## 4. Mantenedor de conductores y días libres

### 4.1 Ver conductores

Menú lateral → **Mantenedor → Conductores**. Muestra la lista con pestañas:

- **Disponibles hoy**: conductores sin restricción para la fecha actual.
- **Con días libres**: conductores con al menos un día libre en los próximos 30 días.
- **Todos**: lista completa.

### 4.2 Registrar días libres

Cada tarjeta de conductor tiene un strip de calendario semanal. Los días tienen tres estados visuales:

- **Fondo blanco** — disponible.
- **Fondo ámbar** — día libre registrado.
- **Fondo rojo** — en operación ese día (asignado automáticamente).

Para agregar un día libre:

1. Ubica al conductor en la lista.
2. Haz clic en **"+ Agregar día libre"** en su tarjeta.
3. Selecciona la fecha (o rango de fechas).
4. Confirma. El día queda en ámbar y el conductor aparecerá como *No disponible* en los formularios de ETA para esa fecha.

Para eliminar un día libre: haz clic sobre el día ámbar → **"Quitar día libre"**.

> **Excepción:** si necesitas asignar un conductor con día libre por emergencia, un usuario con perfil Administrador debe eliminar el día libre desde el mantenedor primero.

---

## 5. Tareas paso a paso

### 5.1 Cargar catálogos base (Administrador / Coordinador)

Menú lateral → **Catálogos**:

1. **Clientes** → Nuevo: nombre, RUT, email, teléfono.
2. **Agentes portuarios** → Nuevo: nombre y sigla.
3. **Contenedores** → Nuevo: código, tipo y estado.
4. **Conductores** → Nuevo: nombre, RUT, teléfono.
5. **Camiones** → Nuevo: patente y marca.

Cada catálogo permite Editar y Eliminar desde la lista.

### 5.2 Crear una ETA (Administrador / Coordinador)

1. Menú lateral → **ETAs** → botón **Nueva ETA**.
2. Completa el formulario: N° ETA, cliente, agente, contenedor, conductor, camión, depósito, fecha/hora de retiro, tipo de proceso, observaciones.
3. Guarda. La ETA nace en estado **Solicitado**.

### 5.3 Avanzar una ETA por el ciclo

En la ficha de detalle de la ETA, panel **Ciclo del contenedor** (lado derecho):

1. El selector **"Avanzar a"** muestra solo los estados válidos para la etapa actual. El color del borde del selector y el chip debajo reflejan el estado seleccionado.
2. Completa los campos según el estado destino:
   - **Almacenado en patio**: solo requiere tipo de contenedor (vacío/con carga), fecha y observación.
   - **Despachado a cliente / Despachado a puerto**: también requiere camión y conductor.
   - **Devuelto a depósito**: solo aparece si el contenedor ya fue despachado al cliente previamente.
3. La **fecha agendada** se pre-llena con la hora actual. Usa las flechas ▲▼ junto a la hora y los minutos (en intervalos de 00/30) para ajustar.
4. Escribe la observación (mensaje al equipo / conductor).
5. Presiona **Registrar movimiento y avanzar estado**.

El movimiento queda registrado en la tabla de **Trazabilidad / movimientos** al pie de la página.

### 5.4 Selección de conductor con disponibilidad filtrada

Al asignar transporte en el formulario de avance, el dropdown de conductor muestra dos grupos:

**✓ Disponibles** (parte superior): conductores sin día libre ni operación activa para la fecha de la operación.

**✗ No disponibles ese día** (parte inferior, en gris): conductores con restricción para esa fecha, con el motivo indicado (*en operación*, *día libre*, etc.). Aparecen visibles para contexto pero se recomienda no seleccionarlos.

### 5.5 Bandeja del Coordinador

Menú lateral → **Bandeja**. Lista las ETAs que están *en puerto* (*Solicitado* / *Asignado*) y aún deben gestionarse.

### 5.6 Tablero de Patio

Menú lateral → **Patio**. Lista los contenedores físicamente en el depósito (*Asignado*, *En patio*, *Almacenado*). Tiene búsqueda inline por contenedor o cliente sin recargar la página.

### 5.7 Recuentos

Menú lateral → **Recuentos**. Muestra por cliente cuántos contenedores están **en puerto** y cuántos **en depósito**.

### 5.8 Reportes y exportación CSV

Menú lateral → **Reportes**. Tres reportes descargables:

- **Retiros**: ETAs en proceso de retiro desde el puerto.
- **Almacenados**: contenedores en depósito.
- **Entregas**: ETAs despachadas o devueltas.

---

## 6. Buscar y filtrar ETAs

En **ETAs**:

- Caja de búsqueda: filtra por N° de ETA, nombre de cliente o código de contenedor.
- Desplegable **Estado**: filtra por etapa del ciclo.
- Los resultados se paginan de a 25.

---

## 7. Preguntas frecuentes

| Pregunta | Respuesta |
|----------|-----------|
| No veo el menú "Catálogos" | Tu rol es *Encargado de Patio*. Solo Administrador y Coordinador editan catálogos. |
| No puedo crear una ETA | Solo Administrador y Coordinador crean ETAs. |
| No aparece "Devuelto a depósito" en el selector | Ese estado solo aparece cuando el contenedor ya fue despachado al cliente. Es el comportamiento esperado. |
| El formulario no deja avanzar | Revisa que todos los campos obligatorios estén completos, incluyendo la fecha agendada y la observación. |
| ¿Puedo deshacer un avance? | No hay retroceso automático. Consulta con el Administrador para corregir desde el panel de administración. |

---

## 8. Glosario

- **ETA**: documento central que representa una operación de contenedor.
- **Agente portuario**: empresa que opera el puerto.
- **Movimiento**: hito operativo registrado para trazabilidad.
- **Estado del ciclo**: etapa de la ETA (Solicitado → … → Despachado a puerto).
- **Día libre**: registro en el mantenedor que bloquea a un conductor para ser asignado en esa fecha.
- **Proceso directo / indirecto**: si el contenedor pasa o no por el depósito.
