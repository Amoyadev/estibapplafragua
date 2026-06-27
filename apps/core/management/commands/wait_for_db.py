"""Espera a que PostgreSQL esté disponible antes de continuar."""
import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Bloquea hasta que la base de datos acepte conexiones."

    def handle(self, *args, **options):
        self.stdout.write("Esperando a la base de datos...")
        max_retries = 30
        for attempt in range(1, max_retries + 1):
            try:
                connections["default"].cursor()
                self.stdout.write(self.style.SUCCESS("Base de datos disponible."))
                return
            except OperationalError:
                self.stdout.write(
                    f"  BD no disponible (intento {attempt}/{max_retries}), reintentando en 1s..."
                )
                time.sleep(1)

        self.stderr.write(self.style.ERROR("No se pudo conectar a la base de datos."))
        raise SystemExit(1)
