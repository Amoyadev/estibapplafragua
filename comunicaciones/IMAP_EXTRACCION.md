# Extracción de correos IMAP — Estibapp

Cuenta operativa: `nfarias@logisticayalmacenaje.cl` (Outlook / Microsoft 365)  
Servidor IMAP: `outlook.office365.com` · Puerto `993` · SSL habilitado

---

## Objetivo

Conectarse vía IMAP al buzón corporativo, extraer los correos entrantes
y filtrar por cliente o puerto para identificar el correo de **"ETA en Secuencia"**,
que es el puntapié inicial del ciclo operativo: indica la fecha en que el
operador logístico debe ir al puerto a retirar el container.

---

## Pseudocódigo en estilo PL/SQL

El siguiente bloque describe la lógica de extracción en lenguaje procedural
(tipo PL/SQL / pseudocódigo estructurado). No es SQL puro, pero sigue la
convención de bloques `DECLARE / BEGIN / EXCEPTION / END` para que sea
legible por el equipo y fácilmente trasladable a Python (`imaplib`) o a
un stored procedure si se integra con base de datos.

```plsql
-- ============================================================
-- PROCEDIMIENTO: EXTRAER_CORREOS_ETA
-- Propósito   : Conectarse al buzón IMAP y extraer correos
--               relevantes para el ciclo de ETAs.
-- ============================================================

PROCEDURE EXTRAER_CORREOS_ETA (
    p_servidor      IN VARCHAR2 DEFAULT 'outlook.office365.com',
    p_puerto        IN NUMBER   DEFAULT 993,
    p_usuario       IN VARCHAR2 DEFAULT 'nfarias@logisticayalmacenaje.cl',
    p_password      IN VARCHAR2,                     -- no hardcodear, usar vault
    p_carpeta       IN VARCHAR2 DEFAULT 'INBOX',
    p_dias_atras    IN NUMBER   DEFAULT 7            -- ventana de búsqueda
)
IS
    v_conexion      IMAP_CONNECTION;
    v_mensajes      CURSOR_MENSAJES;
    v_mensaje       MENSAJE_ROW;
    v_asunto        VARCHAR2(500);
    v_remitente     VARCHAR2(200);
    v_cuerpo        CLOB;
    v_fecha_correo  DATE;
    v_fecha_limite  DATE := SYSDATE - p_dias_atras;

    -- Patrones de filtro
    C_ASUNTO_ETA    CONSTANT VARCHAR2(50) := 'ETA EN SECUENCIA';
    C_ASUNTO_ALT    CONSTANT VARCHAR2(50) := 'ETA SECUENCIA';

BEGIN

    -- 1. Establecer conexión SSL
    v_conexion := IMAP_CONNECT(
        host     => p_servidor,
        port     => p_puerto,
        ssl      => TRUE,
        username => p_usuario,
        password => p_password
    );

    -- 2. Seleccionar carpeta
    IMAP_SELECT_FOLDER(v_conexion, p_carpeta);

    -- 3. Buscar correos dentro de la ventana de tiempo
    --    Criterio IMAP estándar: SINCE fecha y UNSEEN (no leídos)
    v_mensajes := IMAP_SEARCH(
        conn     => v_conexion,
        criteria => 'SINCE ' || TO_CHAR(v_fecha_limite, 'DD-MON-YYYY') ||
                    ' NOT DELETED'
    );

    -- 4. Iterar cada mensaje
    FOR v_mensaje IN v_mensajes LOOP

        v_asunto    := UPPER(TRIM(v_mensaje.subject));
        v_remitente := LOWER(TRIM(v_mensaje.from_address));
        v_fecha_correo := v_mensaje.date_received;
        v_cuerpo    := v_mensaje.body_plain;

        -- 4a. Filtro primario: identificar correo "ETA en Secuencia"
        IF INSTR(v_asunto, C_ASUNTO_ETA) > 0
        OR INSTR(v_asunto, C_ASUNTO_ALT) > 0
        THEN

            -- 4b. Extraer campos clave del cuerpo
            DECLARE
                v_numero_eta    VARCHAR2(30);
                v_cliente       VARCHAR2(150);
                v_puerto        VARCHAR2(60);
                v_fecha_retiro  DATE;
                v_contenedor    VARCHAR2(20);
            BEGIN
                -- Parsear el cuerpo según formato estándar del correo
                -- (ajustar regex según plantilla real del cliente)
                v_numero_eta   := REGEXP_SUBSTR(v_cuerpo, 'ETA[:\s]+([A-Z0-9\-]+)', 1, 1, 'i', 1);
                v_cliente      := REGEXP_SUBSTR(v_cuerpo, 'Cliente[:\s]+(.+?)[\r\n]', 1, 1, 'i', 1);
                v_puerto       := REGEXP_SUBSTR(v_cuerpo, 'Puerto[:\s]+(.+?)[\r\n]', 1, 1, 'i', 1);
                v_contenedor   := REGEXP_SUBSTR(v_cuerpo, '[A-Z]{4}[0-9]{7}', 1, 1);
                v_fecha_retiro := TO_DATE(
                    REGEXP_SUBSTR(v_cuerpo, 'Fecha[:\s]+(\d{2}/\d{2}/\d{4})', 1, 1, 'i', 1),
                    'DD/MM/YYYY'
                );

                -- 4c. Insertar o actualizar en tabla de staging
                MERGE INTO CORREOS_ETA_STAGING tgt
                USING (
                    SELECT
                        v_mensaje.message_id  AS msg_id,
                        v_numero_eta          AS numero_eta,
                        v_cliente             AS cliente,
                        v_puerto              AS puerto,
                        v_contenedor          AS contenedor,
                        v_fecha_retiro        AS fecha_retiro,
                        v_fecha_correo        AS fecha_correo,
                        v_remitente           AS remitente,
                        v_cuerpo              AS cuerpo_original
                    FROM DUAL
                ) src ON (tgt.msg_id = src.msg_id)
                WHEN NOT MATCHED THEN
                    INSERT (msg_id, numero_eta, cliente, puerto, contenedor,
                            fecha_retiro, fecha_correo, remitente, cuerpo_original,
                            estado_procesamiento, creado)
                    VALUES (src.msg_id, src.numero_eta, src.cliente, src.puerto,
                            src.contenedor, src.fecha_retiro, src.fecha_correo,
                            src.remitente, src.cuerpo_original,
                            'PENDIENTE', SYSDATE);

                COMMIT;

                -- 4d. Log de auditoría
                INSERT INTO LOG_CORREOS (fecha, tipo, detalle)
                VALUES (SYSDATE, 'ETA_SECUENCIA',
                        'Correo capturado: ' || v_numero_eta || ' / ' || v_cliente);
                COMMIT;

            EXCEPTION
                WHEN OTHERS THEN
                    -- No abortar el loop si falla un mensaje individual
                    INSERT INTO LOG_CORREOS (fecha, tipo, detalle)
                    VALUES (SYSDATE, 'ERROR',
                            'Msg ' || v_mensaje.message_id || ': ' || SQLERRM);
                    COMMIT;
            END;

        -- 4e. Filtro secundario: otros correos de clientes/puertos de interés
        ELSIF fn_es_cliente_conocido(v_remitente) = TRUE
           OR fn_menciona_puerto(v_asunto, v_cuerpo) = TRUE
        THEN
            -- Guardar en staging genérico para revisión manual
            INSERT INTO CORREOS_GENERALES_STAGING
                (msg_id, asunto, remitente, fecha_correo, estado)
            VALUES
                (v_mensaje.message_id, v_mensaje.subject,
                 v_remitente, v_fecha_correo, 'REVISAR');
            COMMIT;
        END IF;

    END LOOP;

    -- 5. Cerrar conexión
    IMAP_DISCONNECT(v_conexion);

EXCEPTION
    WHEN IMAP_AUTH_ERROR THEN
        RAISE_APPLICATION_ERROR(-20001, 'Error de autenticación IMAP: revisar credenciales.');
    WHEN IMAP_CONNECTION_ERROR THEN
        RAISE_APPLICATION_ERROR(-20002, 'No se pudo conectar al servidor IMAP.');
    WHEN OTHERS THEN
        IMAP_DISCONNECT(v_conexion);
        RAISE;
END EXTRAER_CORREOS_ETA;
```

---

## Tablas de staging sugeridas

```sql
-- Correos "ETA en Secuencia" capturados y parseados
CREATE TABLE CORREOS_ETA_STAGING (
    id                      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    msg_id                  VARCHAR2(200) UNIQUE NOT NULL,
    numero_eta              VARCHAR2(30),
    cliente                 VARCHAR2(150),
    puerto                  VARCHAR2(60),
    contenedor              VARCHAR2(20),
    fecha_retiro            DATE,
    fecha_correo            DATE NOT NULL,
    remitente               VARCHAR2(200),
    cuerpo_original         CLOB,
    estado_procesamiento    VARCHAR2(20) DEFAULT 'PENDIENTE',
    -- Estados: PENDIENTE → PROCESADO → ERROR → IGNORADO
    eta_creada_id           NUMBER,       -- FK a ETA en Estibapp (cuando se cree)
    creado                  DATE DEFAULT SYSDATE,
    procesado               DATE
);

-- Log general de ejecuciones
CREATE TABLE LOG_CORREOS (
    id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha       DATE DEFAULT SYSDATE,
    tipo        VARCHAR2(30),   -- ETA_SECUENCIA | ERROR | GENERAL
    detalle     VARCHAR2(2000)
);
```

---

## Funciones auxiliares requeridas

| Función | Propósito |
|---|---|
| `fn_es_cliente_conocido(email)` | Retorna TRUE si el remitente está en la tabla de clientes |
| `fn_menciona_puerto(asunto, cuerpo)` | Retorna TRUE si el texto menciona TPS, STI, DPW u otro puerto configurado |
| `IMAP_CONNECT / IMAP_DISCONNECT` | Wrappers de conexión (en Python: `imaplib.IMAP4_SSL`) |
| `IMAP_SELECT_FOLDER / IMAP_SEARCH` | Wrappers de selección y búsqueda IMAP |

---

## Implementación en Python (referencia)

```python
import imaplib
import email
from email.header import decode_header

IMAP_HOST = "outlook.office365.com"
IMAP_PORT = 993
USUARIO   = "nfarias@logisticayalmacenaje.cl"
PASSWORD  = "..."  # usar variable de entorno, nunca hardcoded

def extraer_correos_eta():
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(USUARIO, PASSWORD)
    mail.select("INBOX")

    # Buscar correos no eliminados de los últimos 7 días
    _, ids = mail.search(None, 'SINCE "07-Jun-2026" NOT DELETED')

    for num in ids[0].split():
        _, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        asunto_raw, enc = decode_header(msg["Subject"])[0]
        asunto = asunto_raw.decode(enc or "utf-8") if isinstance(asunto_raw, bytes) else asunto_raw

        if "ETA EN SECUENCIA" in asunto.upper() or "ETA SECUENCIA" in asunto.upper():
            # Extraer cuerpo y parsear campos
            cuerpo = _get_body(msg)
            _procesar_eta_secuencia(asunto, msg["From"], cuerpo)

    mail.logout()

def _get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8", errors="ignore")
    return msg.get_payload(decode=True).decode("utf-8", errors="ignore")
```

---

## Notas de seguridad

- La contraseña **nunca** debe estar en el código fuente. Usar variable de entorno `IMAP_PASSWORD` o un vault (AWS Secrets Manager, HashiCorp Vault).
- El acceso IMAP a Microsoft 365 puede requerir habilitar "autenticación básica" o usar OAuth2 con app registration en Azure AD. Verificar política del tenant.
- Rotar la contraseña periódicamente y revocar acceso inmediatamente si hay sospecha de compromiso.

---

## Próximos pasos

- [ ] Integrar `extraer_correos_eta()` como tarea periódica (cron / Celery beat) cada 15 minutos
- [ ] Crear vista en Estibapp que muestre los correos en `CORREOS_ETA_STAGING` con estado `PENDIENTE` para que el coordinador los valide y cree la ETA con un click
- [ ] Definir plantilla exacta del correo "ETA en Secuencia" con el cliente para afinar el parser de regex
- [ ] Módulo WhatsApp: notificación automática al conductor cuando se asigna una ETA con movimiento tipo RETIRO
