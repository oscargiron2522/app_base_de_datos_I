from django.db import models
from django.core.validators import MinValueValidator
from catalogos.models import Liga, EquipoAtleta, TipoMercado
from cuentas.models import Usuario, Administrador
from billetera.models import Billetera


class Evento(models.Model):
    ESTADO_EVENTO_CHOICES = [
        ('PROGRAMADO', 'Programado'),
        ('EN_JUEGO', 'En juego'),
        ('FINALIZADO', 'Finalizado'),
        ('SUSPENDIDO', 'Suspendido'),
        ('CANCELADO', 'Cancelado'),
    ]

    id_evento = models.AutoField(primary_key=True)
    id_liga = models.ForeignKey(Liga, on_delete=models.PROTECT, db_column='id_liga', related_name='eventos')
    id_equipo_local = models.ForeignKey(EquipoAtleta, on_delete=models.PROTECT, db_column='id_equipo_local', related_name='eventos_local')
    id_equipo_visitante = models.ForeignKey(EquipoAtleta, on_delete=models.PROTECT, db_column='id_equipo_visitante', related_name='eventos_visitante')
    fecha_inicio = models.DateTimeField()
    estado_evento = models.CharField(max_length=15, choices=ESTADO_EVENTO_CHOICES, default='PROGRAMADO')

    class Meta:
        db_table = 'tbl_evento'
        verbose_name = 'Evento deportivo'
        verbose_name_plural = 'Eventos deportivos'
        indexes = [models.Index(fields=['fecha_inicio'])]

    def __str__(self):
        return f'{self.id_equipo_local} vs {self.id_equipo_visitante} ({self.fecha_inicio:%Y-%m-%d %H:%M})'


class ResultadoEvento(models.Model):
    id_resultado = models.AutoField(primary_key=True)
    id_evento = models.OneToOneField(Evento, on_delete=models.CASCADE, db_column='id_evento', related_name='resultado')
    puntuacion_local = models.PositiveIntegerField()
    puntuacion_visitante = models.PositiveIntegerField()
    observaciones = models.CharField(max_length=255, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_resultado_evento'
        verbose_name = 'Resultado de evento'
        verbose_name_plural = 'Resultados de eventos'


class MercadoEvento(models.Model):
    ESTADO_MERCADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('CERRADO', 'Cerrado'),
        ('LIQUIDADO', 'Liquidado'),
    ]

    id_mercado_evento = models.AutoField(primary_key=True)
    id_evento = models.ForeignKey(Evento, on_delete=models.CASCADE, db_column='id_evento', related_name='mercados')
    id_tipo_mercado = models.ForeignKey(TipoMercado, on_delete=models.PROTECT, db_column='id_tipo_mercado', related_name='mercados_evento')
    estado_mercado = models.CharField(max_length=10, choices=ESTADO_MERCADO_CHOICES, default='ABIERTO')

    class Meta:
        db_table = 'tbl_mercado_evento'
        verbose_name = 'Mercado de evento'
        verbose_name_plural = 'Mercados de evento'
        unique_together = ('id_evento', 'id_tipo_mercado')


class OpcionApuesta(models.Model):
    id_opcion = models.AutoField(primary_key=True)
    id_mercado_evento = models.ForeignKey(MercadoEvento, on_delete=models.CASCADE, db_column='id_mercado_evento', related_name='opciones')
    descripcion_opcion = models.CharField(max_length=150)
    cuota_actual = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(1.01)])
    es_ganadora = models.BooleanField(default=False)

    class Meta:
        db_table = 'tbl_opcion_apuesta'
        verbose_name = 'Opción de apuesta'
        verbose_name_plural = 'Opciones de apuesta'

    def __str__(self):
        return f'{self.descripcion_opcion} @ {self.cuota_actual}'


class PromocionCuota(models.Model):
    id_promocion = models.AutoField(primary_key=True)
    id_opcion = models.ForeignKey(OpcionApuesta, on_delete=models.CASCADE, db_column='id_opcion', related_name='promociones')
    porcentaje_aumento = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    class Meta:
        db_table = 'tbl_promocion_cuota'
        verbose_name = 'Promoción de cuota (boost)'
        verbose_name_plural = 'Promociones de cuota (boost)'


class Boleto(models.Model):
    ESTADO_BOLETO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('GANADO', 'Ganado'),
        ('PERDIDO', 'Perdido'),
        ('ANULADO', 'Anulado'),
        ('PAGADO', 'Pagado'),
    ]

    id_boleto = models.BigAutoField(primary_key=True)
    id_billetera = models.ForeignKey(Billetera, on_delete=models.PROTECT, db_column='id_billetera', related_name='boletos')
    monto_apostado = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(1)])
    cuota_total = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(1.01)])
    ganancia_potencial = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    estado_boleto = models.CharField(max_length=10, choices=ESTADO_BOLETO_CHOICES, default='PENDIENTE')
    fecha_emision = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_boleto'
        verbose_name = 'Boleto de apuesta'
        verbose_name_plural = 'Boletos de apuesta'

    def es_compuesto(self):
        return self.detalles.count() > 1


class DetalleBoleto(models.Model):
    id_detalle = models.BigAutoField(primary_key=True)
    id_boleto = models.ForeignKey(Boleto, on_delete=models.CASCADE, db_column='id_boleto', related_name='detalles')
    id_opcion = models.ForeignKey(OpcionApuesta, on_delete=models.PROTECT, db_column='id_opcion', related_name='detalles_boleto')
    cuota_momento = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(1.01)])

    class Meta:
        db_table = 'tbl_detalle_boleto'
        verbose_name = 'Detalle de boleto'
        verbose_name_plural = 'Detalles de boleto'
        unique_together = ('id_boleto', 'id_opcion')


class HistorialCuotas(models.Model):
    id_historial_cuota = models.BigAutoField(primary_key=True)
    id_opcion = models.ForeignKey(OpcionApuesta, on_delete=models.CASCADE, db_column='id_opcion', related_name='historial_cuotas')
    cuota_anterior = models.DecimalField(max_digits=6, decimal_places=2)
    cuota_nueva = models.DecimalField(max_digits=6, decimal_places=2)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    id_admin = models.ForeignKey(Administrador, on_delete=models.SET_NULL, db_column='id_admin', related_name='cambios_cuota', blank=True, null=True)

    class Meta:
        db_table = 'tbl_historial_cuotas'
        verbose_name = 'Historial de cuota'
        verbose_name_plural = 'Historial de cuotas'


class HistorialEstadoBoleto(models.Model):
    id_historial_boleto = models.BigAutoField(primary_key=True)
    id_boleto = models.ForeignKey(Boleto, on_delete=models.CASCADE, db_column='id_boleto', related_name='historial_estados')
    estado_anterior = models.CharField(max_length=10, choices=Boleto.ESTADO_BOLETO_CHOICES)
    estado_nuevo = models.CharField(max_length=10, choices=Boleto.ESTADO_BOLETO_CHOICES)
    motivo_cambio = models.CharField(max_length=255, blank=True, null=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_historial_estado_boleto'
        verbose_name = 'Historial de estado de boleto'
        verbose_name_plural = 'Historial de estados de boleto'


class HistorialCambiosEvento(models.Model):
    id_historial_evento = models.BigAutoField(primary_key=True)
    id_evento = models.ForeignKey(Evento, on_delete=models.CASCADE, db_column='id_evento', related_name='historial_cambios')
    estado_anterior = models.CharField(max_length=15, choices=Evento.ESTADO_EVENTO_CHOICES)
    estado_nuevo = models.CharField(max_length=15, choices=Evento.ESTADO_EVENTO_CHOICES)
    minuto_partido = models.PositiveSmallIntegerField(blank=True, null=True)
    marcador_momento = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_historial_cambios_evento'
        verbose_name = 'Historial de cambio de evento'
        verbose_name_plural = 'Historial de cambios de evento'


class HistorialJugadorResumen(models.Model):
    id_resumen = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario', related_name='resumenes_mensuales')
    mes_ano = models.CharField(max_length=7, help_text='Formato AAAA-MM')
    total_boletos_creados = models.PositiveIntegerField(default=0)
    monto_total_apostado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_total_reclamado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    rendimiento_neto = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'tbl_historial_jugador_resumen'
        verbose_name = 'Resumen mensual de jugador'
        verbose_name_plural = 'Resúmenes mensuales de jugador'
        unique_together = ('id_usuario', 'mes_ano')
