# Manual de usuario — EstibAPP

---

## Módulo: Conductores y disponibilidad en operaciones

Este módulo explica cómo gestionar la disponibilidad de conductores desde el mantenedor, cómo esa información se integra al flujo de operaciones, y cómo cambiar el conductor o patente asignado en cada etapa del ciclo de un contenedor.

---

### 1. Mantenedor de conductores — registrar días libres

Accede desde el menú lateral en **Mantenedor → Conductores**.

Cada tarjeta de conductor muestra un strip de calendario semanal con los próximos 7 días. Los días tienen tres estados visuales:

- **Fondo blanco** — disponible, sin restricciones.
- **Fondo ámbar** — día libre registrado. El conductor no puede ser asignado ese día.
- **Fondo rojo** — operación o servicio activo asignado ese día (se marca automáticamente).

**Para registrar un día libre:**

1. Ubica al conductor en la lista.
2. Haz clic en **"+ Agregar día libre"** en la esquina superior derecha del strip de calendario.
3. Selecciona uno o varios días en el selector de fechas. Puedes marcar días individuales o un rango.
4. Confirma. El día queda marcado en ámbar y el conductor aparecerá como "No disponible" en ese período al momento de asignar operaciones.

Para eliminar un día libre, haz clic sobre el día ámbar en el strip y selecciona **"Quitar día libre"**.

> La pestaña **"Disponibles hoy"** en la parte superior filtra la lista mostrando solo conductores sin restricción para la fecha actual. La pestaña **"Con días libres"** muestra todos los que tienen al menos un día libre registrado en los próximos 30 días.

---

### 2. Flujo de operación — selección de conductor con disponibilidad filtrada

Cuando una operación pasa de estado **Pendiente → Asignado**, el sistema requiere asignar un conductor y una patente de camión. En ese momento, el selector de conductores muestra la disponibilidad calculada automáticamente para la fecha de la operación.

**Estructura del dropdown de conductor:**

El listado está dividido en dos secciones:

**Disponibles** (parte superior, seleccionables)
Conductores que cumplen todas las condiciones para esa fecha:
- Sin día libre registrado.
- Sin operación activa asignada.
- Sin servicio de entrega o despacho en curso.

Cada conductor disponible muestra un punto verde y la etiqueta "libre" a la derecha.

**No disponibles** (parte inferior, solo lectura)
Conductores que tienen al menos una restricción para esa fecha. Aparecen al final del listado en tono gris, sin posibilidad de selección, con el motivo indicado a la derecha:
- **"día libre"** — registrado en el mantenedor.
- **"en operación"** — asignado a otro contenedor activo ese día.
- **"servicio activo"** — tiene un servicio de entrega o despacho activo.

> Los conductores no disponibles no pueden seleccionarse, pero son visibles para que el coordinador tenga contexto completo sin cambiar de pantalla.

**Para asignar conductor y patente:**

1. Abre la operación desde la bandeja o desde ETAs.
2. Haz clic en **"Pasar a Asignado"** o en el botón de edición del conductor si ya está en esa etapa.
3. En el panel de asignación, selecciona un conductor del listado de disponibles.
4. La patente del camión se pre-completa automáticamente con el camión asociado al conductor. Puedes cambiarla manualmente si es necesario.
5. Confirma con **"Confirmar asignación"**. El estado del contenedor avanza a **Asignado** y el conductor queda bloqueado para ese día en otros flujos.

---

### 3. Ver en qué etapa está la operación

Desde la vista de ETAs o desde el tablero operativo del día, cada contenedor muestra su etapa actual en forma de badge de estado:

| Estado | Descripción |
|--------|-------------|
| Pendiente | ETA creada, sin conductor asignado |
| Asignado | Conductor y camión confirmados |
| En tránsito | El camión salió a retirar o despachar |
| En patio | El contenedor ingresó al depósito |
| Despachado a cliente | Salida hacia el cliente registrada |
| Despachado a puerto | Salida hacia el puerto registrada |

El historial de etapas — incluyendo quién realizó cada cambio y a qué hora — se puede ver dentro de la operación haciendo clic en **"Ver historial"** en el panel lateral derecho.

---

### 4. Cambiar conductor o patente en una operación activa

Es posible cambiar el conductor o camión asignado en cualquier momento, siempre que la operación no haya finalizado.

**Para cambiar el conductor:**

1. Abre la operación desde ETAs o desde el tablero.
2. En el panel de asignación, haz clic en el nombre del conductor actual. Aparece el mismo dropdown con disponibilidad filtrada para la fecha de esa operación.
3. Selecciona el nuevo conductor. El anterior queda liberado y su disponibilidad se actualiza automáticamente para ese día.
4. Si el nuevo conductor tiene un camión distinto asociado, la patente se actualiza en forma automática. Puedes dejarla o cambiarla manualmente.
5. Guarda los cambios.

> Al cambiar de conductor, el estado del contenedor no retrocede. La operación continúa en la etapa en que estaba, solo cambia quién la ejecuta.

**Para cambiar solo la patente:**

1. Abre la operación y haz clic en la patente actual.
2. Selecciona otra patente del listado de camiones disponibles.
3. Confirma el cambio.

---

### 5. Resumen del flujo combinado

```
Mantenedor → Conductor → Registrar días libres (calendario semanal)
                ↓
Operación → Pasar a "Asignado"
                ↓
Dropdown de conductor (disponibles arriba · no disponibles abajo, sin selección)
                ↓
Confirmar asignación → Estado: Asignado
                ↓
En tránsito → En patio → Despachado
                ↓
Cambiar conductor/patente en cualquier etapa sin retroceder el estado
```

---

> **Nota para el coordinador:** los conductores marcados como "día libre" en el mantenedor no aparecerán disponibles aunque el coordinador los busque manualmente. Si necesitas asignar un conductor con día libre por excepción, un usuario con perfil Administrador puede eliminar el día libre desde el mantenedor antes de confirmar la asignación.
