"""
Modelos del dominio Estiba (MVP 1).
Foco: trazabilidad de contenedores. NO se dimensionan espacios (Fase 2).
"""
from django.db import models


class TimeStampedModel(models.Model):
    """Campos de auditoría comunes."""

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AgentePortuario(TimeStampedModel):
    """Empresa/agente que opera un puerto (licita los puertos)."""

    nombre = models.CharField(max_length=120)
    sigla = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Agente portuario"
        verbose_name_plural = "Agentes portuarios"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.sigla})" if self.sigla else self.nombre


class Empresa(TimeStampedModel):
    """
    Empresa genérica usada como dato normalizado en listas desplegables:
    empresa del conductor (transporte) y empresa responsable de un movimiento.
    Usar catálogos en vez de texto libre evita confusiones en los informes.
    """

    nombre = models.CharField(max_length=120, unique=True)
    rut = models.CharField("RUT", max_length=15, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Cliente(TimeStampedModel):
    """Cliente que reserva/solicita contenedores por correo."""

    nombre = models.CharField(max_length=150)
    rut = models.CharField("RUT", max_length=15, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Conductor(TimeStampedModel):
    """Conductor del camión que mueve el contenedor."""

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INOPERATIVO = "INOPERATIVO", "Inoperativo"

    nombre = models.CharField(max_length=150)
    empresa = models.ForeignKey(
        "Empresa",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conductores",
        help_text="Empresa de transporte a la que pertenece el conductor.",
    )
    rut = models.CharField("RUT", max_length=15, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.ACTIVO,
        help_text="Disponibilidad operativa del conductor (Activo / Inoperativo).",
    )

    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"
        ordering = ["nombre"]

    def __str__(self):
        # Formato "Nombre — Empresa" para identificar de un vistazo en las listas.
        return f"{self.nombre} — {self.empresa}" if self.empresa else self.nombre


class Camion(TimeStampedModel):
    """Camión identificado por patente."""

    patente = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=60, blank=True)

    class Meta:
        verbose_name = "Camión"
        verbose_name_plural = "Camiones"
        ordering = ["patente"]

    def __str__(self):
        return self.patente


class Contenedor(TimeStampedModel):
    """Contenedor traqueado. En MVP1 solo se registran datos, no ubicación física."""

    class Tipo(models.TextChoices):
        DRY_20 = "20DV", "20' Dry"
        DRY_40 = "40DV", "40' Dry"
        HC_40 = "40HC", "40' High Cube"
        REEFER = "REEF", "Reefer"
        OTRO = "OTRO", "Otro"

    class Estado(models.TextChoices):
        VACIO = "VACIO", "Vacío"
        CARGADO = "CARGADO", "Con carga"

    codigo = models.CharField(max_length=15, unique=True)
    tipo = models.CharField(max_length=5, choices=Tipo.choices, default=Tipo.DRY_20)
    estado = models.CharField(max_length=8, choices=Estado.choices, default=Estado.VACIO)

    class Meta:
        verbose_name = "Contenedor"
        verbose_name_plural = "Contenedores"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} [{self.get_tipo_display()}]"


class ETA(TimeStampedModel):
    """
    Documento núcleo del proceso. Asocia cliente, agente, contenedor, conductor
    y camión, y dirige el ciclo de retiro/almacenaje/despacho.
    """

    # ============================================================
    # ESTADOS DEL CICLO DE LA ETA  (EDITABLE — base MVP)
    # ------------------------------------------------------------
    # Formato de cada línea:  NOMBRE = "VALOR_EN_BD", "Etiqueta visible"
    #   - NOMBRE      → identificador en el código (MAYÚSCULAS).
    #   - VALOR_EN_BD → lo que se guarda en PostgreSQL (no cambiar a la ligera).
    #   - Etiqueta    → texto que ve el usuario en pantalla.
    #
    # ➕ PARA AGREGAR UN ESTADO: añade una línea aquí y, si debe ser parte del
    #    avance automático, agrégalo también a la lista FLUJO_ETA (abajo).
    # ✏️  Cambiar SOLO la etiqueta NO requiere migración.
    #    Cambiar el VALOR_EN_BD SÍ requiere `makemigrations` + `migrate`.
    # ============================================================
    class EstadoCiclo(models.TextChoices):
        SOLICITADO = "SOLICITADO", "Solicitado por cliente"
        ASIGNADO = "ASIGNADO", "Asignado"
        EN_PATIO = "EN_PATIO", "En patio"
        ALMACENADO = "ALMACENADO", "Almacenado"
        DESPACHADO_CLIENTE = "DESPACHADO_CLIENTE", "Despachado a cliente"
        DESPACHADO_PUERTO = "DESPACHADO_PUERTO", "Despachado a puerto"
        # EJEMPLO_NUEVO = "EJEMPLO_NUEVO", "Ejemplo nuevo"  # 👈 plantilla para agregar

    class TipoProceso(models.TextChoices):
        DIRECTO = "DIRECTO", "Directo (con almacenaje)"
        INDIRECTO = "INDIRECTO", "Indirecto (solo trazabilidad)"

    # ----- Catálogos operativos reales (de los Excel Retiro/Entregas) -----
    class Operacion(models.TextChoices):
        IMPORTACION = "IMPO", "Importación"
        EXPORTACION = "EXPO", "Exportación"

    class EstadoRetiro(models.TextChoices):
        RETIRADO = "RETIRADO", "Retirado"
        PENDIENTE = "PENDIENTE", "Pendiente"
        CANCELADO = "CANCELADO", "Cancelado"
        REPROGRAMADO = "REPROGRAMADO", "Reprogramado"

    class EstadoEntrega(models.TextChoices):
        ENTREGADO = "ENTREGADO", "Entregado"
        SIN_LLEGADA = "SIN_LLEGADA", "Sin llegada"
        REPROGRAMADO = "REPROGRAMADO", "Reprogramado"
        PENDIENTE = "PENDIENTE", "Pendiente"
        NO_ENTREGADO = "NO_ENTREGADO", "No entregado"

    class OTD(models.TextChoices):
        ON_TIME = "ON_TIME", "On time"
        OFF_TIME = "OFF_TIME", "Off time"
        SIN_LLEGADA = "SIN_LLEGADA", "Sin llegada"

    numero = models.CharField("N° ETA", max_length=30, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="etas")
    agente = models.ForeignKey(
        AgentePortuario, on_delete=models.PROTECT, related_name="etas"
    )
    contenedor = models.ForeignKey(
        Contenedor, on_delete=models.PROTECT, related_name="etas"
    )
    conductor = models.ForeignKey(
        Conductor, on_delete=models.SET_NULL, null=True, blank=True, related_name="etas"
    )
    camion = models.ForeignKey(
        Camion, on_delete=models.SET_NULL, null=True, blank=True, related_name="etas"
    )

    deposito = models.CharField(max_length=120, blank=True, help_text="Ej. Casablanca")
    ubicacion = models.CharField(
        max_length=120,
        blank=True,
        help_text="Ubicación física en patio (calle/piso/nivel). La registra el "
        "jefe de patio cuando el gruero le indica por radio.",
    )
    fecha = models.DateField()
    hora_retiro = models.TimeField(null=True, blank=True)
    tipo_proceso = models.CharField(
        max_length=10, choices=TipoProceso.choices, default=TipoProceso.DIRECTO
    )
    estado = models.CharField(
        max_length=20, choices=EstadoCiclo.choices, default=EstadoCiclo.SOLICITADO
    )
    observaciones = models.TextField(blank=True)

    # ================================================================
    # DATOS OPERATIVOS REALES (de las planillas Retiro/Entregas)
    # El N° de CONTENEDOR es la llave de negocio que enlaza el retiro
    # (sacar del puerto) con la entrega (llevar al cliente + devolución).
    # ================================================================
    despacho = models.CharField(
        max_length=30, blank=True, help_text="N° de despacho del documento operativo."
    )
    operacion = models.CharField(
        max_length=10, choices=Operacion.choices, blank=True,
        help_text="IMPO (importación) / EXPO (exportación).",
    )
    nave = models.CharField(
        max_length=80, blank=True, help_text="Motonave (M/N) en que llegó el contenedor."
    )
    puerto = models.CharField(
        max_length=40, blank=True, help_text="Puerto/terminal de origen (TPS, STI, DPW...)."
    )
    dimension = models.CharField(
        max_length=30, blank=True, help_text="Tipo/dimensión real (ej. '40 HC', '20 DV')."
    )
    peso = models.PositiveIntegerField(
        null=True, blank=True, help_text="Peso en kilogramos."
    )
    direccion_entrega = models.CharField(max_length=200, blank=True)
    deposito_devolucion = models.CharField(
        max_length=80, blank=True, help_text="Depósito donde se devuelve el vacío."
    )
    fecha_retiro = models.DateField(null=True, blank=True)
    fecha_entrega = models.DateField(null=True, blank=True)
    horario = models.TimeField(
        null=True, blank=True, help_text="Hora de servicio (retiro/entrega)."
    )
    estado_retiro = models.CharField(
        max_length=14, choices=EstadoRetiro.choices, blank=True
    )
    estado_entrega = models.CharField(
        max_length=14, choices=EstadoEntrega.choices, blank=True
    )
    otd = models.CharField(
        max_length=12, choices=OTD.choices, blank=True,
        help_text="Cumplimiento de horario del servicio (On time / Off time).",
    )

    class Meta:
        verbose_name = "ETA"
        verbose_name_plural = "ETAs"
        ordering = ["-fecha", "-creado"]

    def __str__(self):
        return f"ETA {self.numero} · {self.cliente}"

    def estado_siguiente(self):
        """Devuelve el siguiente estado del ciclo, o None si es el último.

        El ciclo NO es estrictamente lineal: tras "Despachado a cliente" el
        contenedor vuelve a "Almacenado" (devuelto a depósito) antes del cierre
        final "Despachado a puerto". Por eso el avance se calcula sobre los
        PASOS del ciclo (FLUJO_PASOS), no sobre la lista de estados únicos.
        """
        idx = self.paso_actual_idx()
        if idx == -1 or idx + 1 >= len(FLUJO_PASOS):
            return None
        return FLUJO_PASOS[idx + 1]["estado"]

    def paso_actual_idx(self):
        """Índice del paso actual dentro de FLUJO_PASOS.

        ``ALMACENADO`` aparece dos veces (almacenaje inicial y retorno del
        cliente); se distingue por la existencia de un movimiento de despacho
        a cliente previo.
        """
        E = self.EstadoCiclo
        if self.estado == E.ALMACENADO and self.ya_despachado_a_cliente():
            return 5  # "Devuelto a depósito" (retorno)
        for i, paso in enumerate(FLUJO_PASOS):
            if paso["estado"] == self.estado:
                return i
        return -1

    def ya_despachado_a_cliente(self):
        """True si la ETA ya registró un despacho a cliente (ida realizada)."""
        if self.pk is None:
            return False
        return self.movimientos.filter(
            tipo=Movimiento.Tipo.DESPACHO_CLIENTE
        ).exists()

    def ubicacion_fisica(self):
        """Ubicación física del contenedor derivada del estado (trazabilidad)."""
        E = self.EstadoCiclo
        if self.estado in (E.SOLICITADO, E.ASIGNADO):
            return "Puerto (origen)"
        if self.estado in ESTADOS_EN_DEPOSITO:
            return "Depósito"
        if self.estado == E.DESPACHADO_CLIENTE:
            return "En cliente"
        if self.estado == E.DESPACHADO_PUERTO:
            return "Puerto (final)"
        return "—"

    def en_deposito(self):
        return self.estado in ESTADOS_EN_DEPOSITO

    def en_cierre(self):
        """True si el contenedor está fuera del depósito (cierre parcial o final)."""
        return self.estado in ESTADOS_CIERRE

    def esta_cerrada(self):
        """Cierre final: el contenedor fue devuelto a puerto (fin del ciclo)."""
        return self.estado == self.EstadoCiclo.DESPACHADO_PUERTO


class Movimiento(TimeStampedModel):
    """Registro de cada hito operativo de una ETA (trazabilidad)."""

    # ============================================================
    # TIPOS DE MOVIMIENTO  (EDITABLE — base MVP)
    # Mismo formato que los estados: NOMBRE = "VALOR_BD", "Etiqueta".
    # ➕ Para agregar un tipo (ej. inspección), añade una línea aquí.
    # ============================================================
    class Tipo(models.TextChoices):
        RETIRO = "RETIRO", "Retiro"
        ALMACENAJE = "ALMACENAJE", "Almacenaje"
        DESPACHO_CLIENTE = "DESPACHO_CLIENTE", "Despacho a cliente"
        RETORNO = "RETORNO", "Devuelto a depósito"
        DESPACHO_PUERTO = "DESPACHO_PUERTO", "Despacho a puerto"
        # INSPECCION = "INSPECCION", "Inspección"  # 👈 plantilla para agregar

    eta = models.ForeignKey(ETA, on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    fecha = models.DateTimeField()
    empresa_responsable = models.ForeignKey(
        "Empresa",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos",
        help_text="Empresa responsable del movimiento (lista desplegable).",
    )
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.eta.numero}"


# ================================================================
# FLUJO OPERATIVO DE LA ETA  (EDITABLE — base MVP)
# ----------------------------------------------------------------
# El ciclo NO es lineal: el contenedor sale a cliente (cierre parcial) y
# RETORNA al depósito (vuelve a ALMACENADO) antes del cierre final
# "Despachado a puerto". Por eso el avance se modela como una lista de PASOS,
# no de estados únicos. Cada paso define:
#   - estado : estado de la ETA al llegar a ese paso (ETA.EstadoCiclo)
#   - mov    : movimiento que se registra al ENTRAR al paso (o None)
#   - label  : etiqueta para el stepper de la tarjeta
# El foco del ciclo es TRAZAR EL CONTENEDOR: ver dónde está físicamente.
# ================================================================
FLUJO_PASOS = [
    {"estado": ETA.EstadoCiclo.SOLICITADO, "mov": None, "label": "Solicitado por cliente"},
    {"estado": ETA.EstadoCiclo.ASIGNADO, "mov": None, "label": "Asignado"},
    {"estado": ETA.EstadoCiclo.EN_PATIO, "mov": Movimiento.Tipo.RETIRO, "label": "En patio"},
    {"estado": ETA.EstadoCiclo.ALMACENADO, "mov": Movimiento.Tipo.ALMACENAJE, "label": "Almacenado"},
    {"estado": ETA.EstadoCiclo.DESPACHADO_CLIENTE, "mov": Movimiento.Tipo.DESPACHO_CLIENTE, "label": "Despachado a cliente"},
    {"estado": ETA.EstadoCiclo.ALMACENADO, "mov": Movimiento.Tipo.RETORNO, "label": "Devuelto a depósito"},
    {"estado": ETA.EstadoCiclo.DESPACHADO_PUERTO, "mov": Movimiento.Tipo.DESPACHO_PUERTO, "label": "Despachado a puerto"},
]

# Lista de estados únicos en orden (selects/filtros). El retorno reutiliza
# ALMACENADO, por eso no se repite aquí.
FLUJO_ETA = [
    ETA.EstadoCiclo.SOLICITADO,
    ETA.EstadoCiclo.ASIGNADO,
    ETA.EstadoCiclo.EN_PATIO,
    ETA.EstadoCiclo.ALMACENADO,
    ETA.EstadoCiclo.DESPACHADO_CLIENTE,
    ETA.EstadoCiclo.DESPACHADO_PUERTO,
]

# Estados en los que el contenedor está físicamente EN EL DEPÓSITO. EDITABLE.
ESTADOS_EN_DEPOSITO = [ETA.EstadoCiclo.EN_PATIO, ETA.EstadoCiclo.ALMACENADO]
# Estados en puerto de ORIGEN (aún no ingresa al depósito).
ESTADOS_EN_PUERTO = [ETA.EstadoCiclo.SOLICITADO, ETA.EstadoCiclo.ASIGNADO]
# Estados de CIERRE: el contenedor está fuera del depósito.
#   - cierre parcial: DESPACHADO_CLIENTE (retornará tras descarga)
#   - cierre final:   DESPACHADO_PUERTO (fin del ciclo del contenedor)
ESTADOS_CIERRE = [
    ETA.EstadoCiclo.DESPACHADO_CLIENTE,
    ETA.EstadoCiclo.DESPACHADO_PUERTO,
]

