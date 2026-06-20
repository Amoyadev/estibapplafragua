# 📊 Reportes y Gráficos — Lógica de negocio (Estibapp)

> Documento vivo. Define **qué** se mide, **de dónde** sale el dato y **cómo** se
> calcula cada gráfico de la sección *Reportes*. Pensado para que en el futuro
> una IA (o una persona) pueda razonar sobre los informes sin tener que leer el
> código: aquí está el "por qué" detrás de cada visualización.

---

## 1. Fuentes de datos

Todos los gráficos se construyen a partir de dos modelos del dominio
(`apps/operaciones/models.py`):

| Modelo | Rol | Campos clave para análisis |
|--------|-----|----------------------------|
| `ETA` | Documento núcleo del ciclo retiro→almacenaje→despacho. | `cliente`, `agente`, `contenedor`, `deposito`, `ubicacion`, `estado`, `fecha`, `creado` |
| `Movimiento` | Hito operativo de una ETA (trazabilidad). | `eta`, `tipo` (RETIRO/ALMACENAJE/DESPACHO_CLIENTE/RETORNO/DESPACHO_PUERTO), `fecha`, `empresa_responsable` |

Conjuntos de estados (definidos y editables en el modelo):

- **En depósito** (`ESTADOS_EN_DEPOSITO`): `EN_PATIO`, `ALMACENADO` → el contenedor está físicamente en el patio.
- **En puerto** (`ESTADOS_EN_PUERTO`): `SOLICITADO`, `ASIGNADO`.
- **Cierre** (`ESTADOS_CIERRE`): `DESPACHADO_CLIENTE` (cierre parcial), `DESPACHADO_PUERTO` (cierre final) → el contenedor está **fuera del depósito**.

> Principio rector: el ciclo traza al **contenedor**, no "cierra" la ETA. No
> existe estado `CERRADO`. Un contenedor entregado a cliente (cierre parcial)
> **vuelve** al depósito tras la descarga; uno devuelto a puerto (cierre final)
> termina el ciclo.

---

## 2. Catálogo de gráficos (sección Reportes)

Cada gráfico responde una pregunta operativa concreta. Implementados con
**Chart.js** (CDN, sin dependencias de build).

### G1 · Contenedores en depósito por cliente — *barras*
- **Pregunta:** ¿quién concentra la ocupación del patio ahora mismo?
- **Cálculo:** `Cliente` anotado con `Count(etas WHERE estado IN ESTADOS_EN_DEPOSITO)`, ordenado desc.
- **Lectura:** un cliente dominante (p. ej. Tattersall ~47%) indica dependencia y prioridad de espacio.

### G2 · Tiempo promedio por etapa — *barras horizontales*
- **Pregunta:** ¿dónde está el cuello de botella del ciclo?
- **Cálculo:** por cada ETA se toman las fechas de sus `Movimiento` y se mide el
  delta entre transiciones consecutivas:
  - `Retiro → Almacenaje`
  - `Almacenaje → Despacho cliente`
  - `Despacho cliente → Retorno`
  - `Retorno → Despacho puerto`
  Se promedia en **días** sobre todas las ETAs que tengan ambas marcas.
- **Lectura:** la barra más larga es la etapa más lenta.

### G3 · Movimientos por agente portuario — *barras*
- **Pregunta:** ¿con qué agente (TPS/STI/PCE/…) se opera más volumen?
- **Cálculo:** `Movimiento` agrupado por `eta.agente.nombre`, `Count`.
- **Lectura:** insumo para negociación de tarifas y SLA por agente.

### G4 · Carga operativa por depósito y tipo — *barras apiladas*
- **Pregunta:** ¿cómo se reparte la ocupación entre depósitos y por tipo de contenedor?
- **Cálculo:** `ETA WHERE estado IN ESTADOS_EN_DEPOSITO`, agrupado por
  `deposito` × `contenedor.tipo` (20'/40'/HC/Reefer). Cada tipo es una serie apilada.
- **Lectura:** detecta saturación de un depósito o exceso de un tipo (p. ej. Reefer).

### G5 · Retiros vs despachos en el tiempo — *líneas*
- **Pregunta:** ¿entran más contenedores de los que salen? (saturación futura)
- **Cálculo:** `Movimiento` tipo `RETIRO`, `DESPACHO_CLIENTE` y `DESPACHO_PUERTO`,
  agrupados por día (`TruncDate(fecha)`), tres series.
- **Lectura:** si la línea de retiros se despega de las de despachos, el patio se
  llena. Distinguir despacho a cliente (retornará) de despacho a puerto (salida
  definitiva) ayuda a anticipar el retorno de contenedores al depósito.

---

## 3. Cómo agregar un gráfico nuevo

1. **Define la pregunta** de negocio (qué decisión habilita).
2. **Identifica la fuente**: ¿`ETA`, `Movimiento`, o un cruce? ¿qué estados?
3. **Agrega el cálculo** en `apps/operaciones/views.py` → `Reportes.get_context_data`,
   devolviendo `{labels, data}` (o `datasets` para apiladas) dentro del dict `graficos`.
4. **Renderiza** en `apps/operaciones/templates/operaciones/reportes.html`:
   un `<canvas>` + un bloque Chart.js que lee el JSON con `{{ graficos|json_script:"graficos-data" }}`.
5. **Documenta aquí** el nuevo gráfico (G6, G7…) con su pregunta y cálculo.

---

## 4. Ideas backlog (Fase 2)

- Ocupación por **ubicación física** (calle/nivel) cuando se seccione el
  almacenaje por ID de contenedor.
- **Lead time** cliente→despacho por agente (boxplot / percentiles).
- Tasa de **devoluciones a puerto tardías** por cliente.
- Exportable a CSV/PDF de cada gráfico (hoy ya hay export CSV de listados).
