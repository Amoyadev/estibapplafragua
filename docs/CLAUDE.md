# Trabajar con Claude en Estibapp

Manual práctico para colaborar con Claude (Cowork) en el día a día del proyecto.

---

## 1. Qué puede hacer Claude en este proyecto

Claude tiene acceso completo a la carpeta `APP/`. Puede leer, editar y crear archivos,
ejecutar comandos de shell (Docker, Git, Python), y razonar sobre el código.

Ejemplos de lo que puedes pedirle:

- "Explícame qué hace `apps/operaciones/views.py`."
- "¿Qué hay de diferente entre la rama `main` y `feature/reportes`?"
- "Agrega un campo `observaciones` al modelo `ETA` y haz la migración."
- "¿Por qué me sale error 502 cuando levanto con Docker?"
- "Revisa si hay lógica duplicada en las vistas de `operaciones`."

---

## 2. Explorar ramas del proyecto

### Ver todas las ramas

Puedes pedirle directamente:

> "¿Qué ramas existen en el proyecto?"

Claude ejecutará internamente:
```bash
git branch -a        # ramas locales y remotas
git log --oneline -10  # últimos commits
```

### Ver qué hay en una rama específica

> "Muéstrame los archivos que cambiaron en la rama `feature/exportaciones`."

Claude hará:
```bash
git diff main..feature/exportaciones --name-only
```

> "Muéstrame el contenido del archivo `views.py` en la rama `feature/exportaciones`."

```bash
git show feature/exportaciones:apps/operaciones/views.py
```

### Cambiar de rama para revisar código

> "Cambia a la rama `feature/exportaciones` y revísame cómo está el módulo de reportes."

Claude hará:
```bash
git checkout feature/exportaciones
```
y luego leerá los archivos relevantes.

> ⚠️ Si tienes cambios sin guardar, avísale antes: "tengo cambios sin commitear, ¿cómo procedo?".

### Comparar ramas

> "¿Qué diferencias hay entre `main` y `feature/exportaciones`?"

```bash
git diff main..feature/exportaciones
git log main..feature/exportaciones --oneline
```

### Volver a `main`

> "Vuelve a la rama principal."

```bash
git checkout main
```

---

## 3. Explorar carpetas del proyecto

No necesitas navegadores de archivos. Basta con describir qué buscas:

| Lo que quieres | Qué decirle a Claude |
|----------------|----------------------|
| Ver la estructura general | "¿Cómo está organizado el proyecto?" |
| Entender un módulo | "Explícame qué hace la app `operaciones`." |
| Buscar dónde está algo | "¿Dónde se define el modelo `ETA`?" |
| Listar archivos de una carpeta | "¿Qué archivos hay en `apps/operaciones/`?" |
| Ver un archivo específico | "Muéstrame `apps/operaciones/models.py`." |

### Estructura principal del proyecto

```
APP/
├── config/             → Configuración Django (settings/base, dev, prod; wsgi)
├── apps/
│   ├── operaciones/    → Módulo principal: ETAs, movimientos, patio, catálogos
│   ├── auditoria/      → Registro de cambios automático
│   └── core/           → Utilidades compartidas (mixins, permisos)
├── templates/          → HTML de todas las vistas
├── static/             → CSS, JS, imágenes del proyecto
├── nginx/              → Configuración de Nginx
├── docs/               → Documentación del proyecto (estás aquí)
├── docker-compose.yml  → Orquestación de servicios
├── Dockerfile          → Imagen de la app
└── .env                → Variables de entorno (no en Git)
```

---

## 4. Pedirle revisiones de código

### Revisar un archivo

> "Revisa `apps/operaciones/views.py` y dime si hay algo que mejorar."

### Revisar antes de hacer un commit

> "Voy a hacer commit de estos cambios, ¿ves algún problema?"

Claude revisará los archivos modificados (`git diff`) y te dará su opinión antes de que confirmes.

### Revisar una rama entera antes de mergear

> "Voy a mergear `feature/exportaciones` a `main`. Revisa los cambios y dime si hay riesgos."

Claude comparará las ramas y señalará: lógica nueva, cambios en modelos/migraciones,
posibles conflictos, cosas que podrían romperse.

### Buscar problemas específicos

> "¿Hay consultas a la base de datos que puedan ser lentas en `views.py`?"
> "¿Las vistas verifican permisos correctamente?"
> "¿Hay código duplicado entre `operaciones` y `core`?"

---

## 5. Trabajar con Git desde Claude

Claude puede ejecutar todos los comandos de Git por ti. Ejemplos de lo que puedes pedirle:

```
"Haz commit de los cambios con el mensaje 'feat: exportación CSV de ETAs'."
"Crea una rama nueva llamada feature/notificaciones."
"¿Cuál fue el último commit en main?"
"¿Qué archivos cambié desde el último commit?"
"Muéstrame el historial de commits de la semana pasada."
```

### Convención de commits usada en este proyecto

```
feat:   nueva funcionalidad
fix:    corrección de bug
config: cambio de configuración
docs:   cambio en documentación
refactor: reorganización de código sin cambiar comportamiento
```

---

## 6. Trabajar con Docker desde Claude

Claude puede operar Docker directamente. No tienes que abrir terminal:

```
"Levanta la app."                    → docker compose up -d
"Para la app."                       → docker compose down
"Muéstrame los logs de la app."      → docker compose logs -f web
"¿Están corriendo los contenedores?" → docker compose ps
"Aplica las migraciones."            → docker compose exec web python manage.py migrate
"Carga los datos de prueba."         → docker compose exec web python manage.py seed_demo
```

---

## 7. Consejos para pedirle cosas a Claude

**Se específico con el archivo o módulo:**
- ✅ "Revisa `apps/operaciones/models.py`, específicamente el modelo `ETA`."
- ❌ "Revisa el código."

**Dale contexto si lo hay:**
- ✅ "Me sale este error al levantar Docker: [pega el error]. ¿Qué lo causa?"
- ❌ "No funciona."

**Dile qué quieres que haga, no solo qué busca:**
- ✅ "Encuentra dónde se calcula el estado de la ETA y explícame la lógica."
- ✅ "Encuentra dónde se calcula el estado de la ETA y cámbialo para que también acepte el estado `Cancelado`."

**Para revisar ramas, siempre di el nombre exacto:**
- ✅ "Revisa la rama `feature/exportaciones`."
- ❌ "Revisa la rama de exportaciones." (Claude puede adivinar, pero mejor ser exacto)

---

## 8. Cosas que Claude NO hace solo (te pregunta antes)

- Borrar archivos o carpetas.
- Hacer `git push` a producción.
- Ejecutar comandos que modifiquen la base de datos de producción.
- Cambiar credenciales en `.env`.

Para todo esto, Claude te mostrará el comando y te pedirá confirmación.
