from django.db import models


class BitacoraSeguridad(models.Model):
    """Registro de eventos de seguridad detectados a nivel de aplicación:
    intentos de inyección SQL, patrones de fuerza bruta / DDOS, valores
    negativos o fuera de rango, entre otros."""

    TIPO_EVENTO_CHOICES = [
        ('SQLI', 'Intento de inyección SQL'),
        ('DDOS', 'Posible ataque de denegación de servicio'),
        ('VALOR_INVALIDO', 'Valor numérico inválido/negativo'),
        ('RATE_LIMIT', 'Límite de solicitudes excedido'),
        ('ACCESO_NO_AUTORIZADO', 'Acceso no autorizado'),
        ('OTRO', 'Otro'),
    ]

    id_bitacora = models.BigAutoField(primary_key=True)
    tipo_evento = models.CharField(max_length=25, choices=TIPO_EVENTO_CHOICES)
    ip_origen = models.GenericIPAddressField()
    ruta_solicitada = models.CharField(max_length=255)
    detalle = models.TextField(blank=True, null=True)
    bloqueado = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_bitacora_seguridad'
        verbose_name = 'Bitácora de seguridad'
        verbose_name_plural = 'Bitácoras de seguridad'
        indexes = [
            models.Index(fields=['ip_origen', 'fecha_registro']),
            models.Index(fields=['tipo_evento']),
        ]

    def __str__(self):
        return f'{self.tipo_evento} desde {self.ip_origen}'
