"""
App de auditoría / trazabilidad de Estibapp.

Responsabilidad única: registrar QUIÉN hizo QUÉ y CUÁNDO, tanto en base de
datos (modelo RegistroAuditoria, consultable desde el admin/reportes) como en
archivos .log rotados (para operación e incidentes). Está aislada del dominio
para poder evolucionar sin tocar `operaciones`.
"""
