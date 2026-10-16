from django.db import models
from django.core.validators import MinValueValidator
from catalogos.models import Estado, MetodoPago
from cuentas.models import Usuario


class Billetera(models.Model):
    id_billetera = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='id_usuario', related_name='billetera')
    saldo_disponible = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    saldo_retenido = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    id_estado = models.ForeignKey(Estado, on_delete=models.PROTECT, db_column='id_estado', related_name='billeteras')

    class Meta:
        db_table = 'tbl_billetera'
        verbose_name = 'Billetera virtual'
        verbose_name_plural = 'Billeteras virtuales'

    def saldo_total(self):
        return self.saldo_disponible + self.saldo_retenido

    def __str__(self):
        return f'Billetera de {self.id_usuario}'


class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('DEPOSITO', 'Depósito'),
        ('RETIRO', 'Retiro'),
        ('APUESTA', 'Débito por apuesta'),
        ('PREMIO', 'Crédito por premio'),
        ('AJUSTE', 'Ajuste administrativo'),
    ]

    id_transaccion = models.BigAutoField(primary_key=True)
    id_billetera = models.ForeignKey(Billetera, on_delete=models.CASCADE, db_column='id_billetera', related_name='transacciones')
    id_metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT, db_column='id_metodo_pago', related_name='transacciones', blank=True, null=True)
    tipo_transaccion = models.CharField(max_length=10, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0.01)])
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_transaccion'
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'


class CuentaBancariaUsuario(models.Model):
    TIPO_CUENTA_CHOICES = [('MONETARIA', 'Monetaria'), ('AHORRO', 'Ahorro')]

    id_cuenta_bancaria = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario', related_name='cuentas_bancarias')
    nombre_banco = models.CharField(max_length=100)
    numero_cuenta = models.CharField(max_length=40)
    tipo_cuenta = models.CharField(max_length=10, choices=TIPO_CUENTA_CHOICES)

    class Meta:
        db_table = 'tbl_cuenta_bancaria_usuario'
        verbose_name = 'Cuenta bancaria de usuario'
        verbose_name_plural = 'Cuentas bancarias de usuario'


class SolicitudRetiro(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('PAGADA', 'Pagada'),
    ]

    id_solicitud = models.AutoField(primary_key=True)
    id_billetera = models.ForeignKey(Billetera, on_delete=models.CASCADE, db_column='id_billetera', related_name='solicitudes_retiro')
    id_cuenta_bancaria = models.ForeignKey(CuentaBancariaUsuario, on_delete=models.PROTECT, db_column='id_cuenta_bancaria', related_name='solicitudes_retiro')
    monto_solicitado = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0.01)])
    estado_solicitud = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_solicitud_retiro'
        verbose_name = 'Solicitud de retiro'
        verbose_name_plural = 'Solicitudes de retiro'


class HistorialSaldoBilletera(models.Model):
    TIPO_OPERACION_CHOICES = [
        ('DEPOSITO', 'Depósito'),
        ('RETIRO', 'Retiro'),
        ('DEBITO_APUESTA', 'Débito por apuesta'),
        ('CREDITO_PREMIO', 'Crédito por premio'),
        ('RETENCION', 'Retención de saldo'),
        ('LIBERACION', 'Liberación de saldo'),
        ('AJUSTE_ADMIN', 'Ajuste administrativo'),
    ]

    id_historial_saldo = models.BigAutoField(primary_key=True)
    id_billetera = models.ForeignKey(Billetera, on_delete=models.CASCADE, db_column='id_billetera', related_name='historial_saldo')
    saldo_anterior = models.DecimalField(max_digits=14, decimal_places=2)
    saldo_nuevo = models.DecimalField(max_digits=14, decimal_places=2)
    monto_movimiento = models.DecimalField(max_digits=14, decimal_places=2)
    tipo_operacion = models.CharField(max_length=20, choices=TIPO_OPERACION_CHOICES)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_historial_saldo_billetera'
        verbose_name = 'Historial de saldo'
        verbose_name_plural = 'Historial de saldos'
