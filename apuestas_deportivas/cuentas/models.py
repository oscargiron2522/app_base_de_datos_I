import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from catalogos.models import Pais, Departamento, Municipio, Estado


class Login(models.Model):
    """Credenciales únicas del sistema (tbl_login). Un login puede pertenecer a
    un usuario final, un administrador o un super administrador (tipo_usuario)."""

    TIPO_USUARIO_CHOICES = [
        ('USUARIO', 'Usuario final'),
        ('ADMIN', 'Administrador'),
        ('SUPER_ADMIN', 'Super administrador'),
    ]

    id_login = models.AutoField(primary_key=True)
    id_sistema_us = models.CharField(max_length=50, unique=True, help_text='Identificador único de sistema (correo o usuario).')
    nombre_usuario = models.CharField(max_length=100, unique=True)
    contrasena_usuario = models.CharField(max_length=255)  # se guarda con hash (PBKDF2/Argon2 vía Django)
    tipo_usuario = models.CharField(max_length=15, choices=TIPO_USUARIO_CHOICES)
    fecha_registro_login = models.DateTimeField(auto_now_add=True)

    # Campos de control de seguridad (fuerza bruta / bloqueo)
    intentos_fallidos = models.PositiveSmallIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    ultimo_cambio_password = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tbl_login'
        verbose_name = 'Login'
        verbose_name_plural = 'Logins'

    def set_password(self, raw_password):
        self.contrasena_usuario = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.contrasena_usuario)

    def __str__(self):
        return self.nombre_usuario


class LoginLog(models.Model):
    id_login_log = models.AutoField(primary_key=True)
    id_login = models.ForeignKey(Login, on_delete=models.CASCADE, db_column='id_login', related_name='logs')
    fecha_registro_log_us = models.DateTimeField(auto_now_add=True)
    ip_acceso = models.GenericIPAddressField()

    class Meta:
        db_table = 'tbl_login_log'
        verbose_name = 'Bitácora de login'
        verbose_name_plural = 'Bitácoras de login'


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    id_login = models.OneToOneField(Login, on_delete=models.CASCADE, db_column='id_login', related_name='usuario')
    primer_nombre_us = models.CharField(max_length=80)
    segundo_nombre_us = models.CharField(max_length=80, blank=True, null=True)
    primer_apellido_us = models.CharField(max_length=80)
    segundo_apellido_us = models.CharField(max_length=80, blank=True, null=True)
    apellido_casada_us = models.CharField(max_length=80, blank=True, null=True)
    fecha_nacimiento_us = models.DateField()
    id_departamento_us = models.ForeignKey(Departamento, on_delete=models.PROTECT, db_column='id_departamento_us', related_name='usuarios')
    id_municipio_us = models.ForeignKey(Municipio, on_delete=models.PROTECT, db_column='id_municipio_us', related_name='usuarios')
    direccion_us = models.CharField(max_length=255)
    correo_us = models.EmailField(unique=True)
    telefono_us = models.CharField(max_length=20)
    id_estado = models.ForeignKey(Estado, on_delete=models.PROTECT, db_column='id_estado', related_name='usuarios')

    class Meta:
        db_table = 'tbl_usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def nombre_completo(self):
        partes = [self.primer_nombre_us, self.segundo_nombre_us, self.primer_apellido_us,
                  self.segundo_apellido_us, self.apellido_casada_us]
        return ' '.join([p for p in partes if p])

    def __str__(self):
        return self.nombre_completo()


class Administrador(models.Model):
    id_admin = models.AutoField(primary_key=True)
    id_login = models.OneToOneField(Login, on_delete=models.CASCADE, db_column='id_login', related_name='administrador')
    codigo_empleado = models.CharField(max_length=30, unique=True)
    primer_nombre_admin = models.CharField(max_length=80)
    primer_apellido_admin = models.CharField(max_length=80)
    departamento_empresa = models.CharField(max_length=100)
    correo_corporativo = models.EmailField()
    rol_administrativo = models.CharField(
        max_length=20,
        choices=[
            ('OPERADOR_EVENTOS', 'Operador de eventos'),
            ('CAJERO', 'Cajero'),
            ('AUDITOR', 'Auditor'),
        ],
        default='OPERADOR_EVENTOS',
        help_text='Rol estricto según seguridad financiera del sistema.'
    )
    id_estado = models.ForeignKey(Estado, on_delete=models.PROTECT, db_column='id_estado', related_name='administradores')

    class Meta:
        db_table = 'tbl_administrador'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return f'{self.primer_nombre_admin} {self.primer_apellido_admin}'


class SuperAdministrador(models.Model):
    id_super_admin = models.AutoField(primary_key=True)
    id_login = models.OneToOneField(Login, on_delete=models.CASCADE, db_column='id_login', related_name='super_administrador')
    nombre_completo = models.CharField(max_length=150)
    correo_maestro = models.EmailField()
    llave_mfa_secret = models.CharField(max_length=64, blank=True, null=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_super_administrador'
        verbose_name = 'Super administrador'
        verbose_name_plural = 'Super administradores'

    def __str__(self):
        return self.nombre_completo


class PreguntaSeguridad(models.Model):
    """Catálogo de preguntas de seguridad usadas en la recuperación de contraseña."""
    id_pregunta = models.AutoField(primary_key=True)
    texto_pregunta = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_pregunta_seguridad'
        verbose_name = 'Pregunta de seguridad'
        verbose_name_plural = 'Preguntas de seguridad'

    def __str__(self):
        return self.texto_pregunta


class UsuarioPreguntaSeguridad(models.Model):
    """Respuestas (hash) que el login configuró para poder recuperar su contraseña."""
    id_usuario_pregunta = models.AutoField(primary_key=True)
    id_login = models.ForeignKey(Login, on_delete=models.CASCADE, db_column='id_login', related_name='preguntas_seguridad')
    id_pregunta = models.ForeignKey(PreguntaSeguridad, on_delete=models.PROTECT, db_column='id_pregunta')
    respuesta_hash = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_usuario_pregunta_seguridad'
        verbose_name = 'Respuesta de seguridad'
        verbose_name_plural = 'Respuestas de seguridad'
        unique_together = ('id_login', 'id_pregunta')

    def set_respuesta(self, raw_respuesta):
        self.respuesta_hash = make_password(raw_respuesta.strip().lower())

    def check_respuesta(self, raw_respuesta):
        return check_password(raw_respuesta.strip().lower(), self.respuesta_hash)


class RecuperacionPassword(models.Model):
    """Token temporal enviado por correo para restablecer contraseña."""
    id_recuperacion = models.AutoField(primary_key=True)
    id_login = models.ForeignKey(Login, on_delete=models.CASCADE, db_column='id_login', related_name='recuperaciones')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)
    ip_solicitud = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'tbl_recuperacion_password'
        verbose_name = 'Recuperación de contraseña'
        verbose_name_plural = 'Recuperaciones de contraseña'


class AdminLog(models.Model):
    id_admin_log = models.BigAutoField(primary_key=True)
    id_login = models.ForeignKey(Login, on_delete=models.CASCADE, db_column='id_login', related_name='acciones_admin')
    accion_realizada = models.CharField(max_length=255)
    tabla_afectada = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_admin_log'
        verbose_name = 'Bitácora de administración'
        verbose_name_plural = 'Bitácoras de administración'


class HistorialSesiones(models.Model):
    RESULTADO_CHOICES = [('EXITOSO', 'Exitoso'), ('FALLIDO', 'Fallido')]

    id_historial_sesion = models.BigAutoField(primary_key=True)
    id_login = models.ForeignKey(Login, on_delete=models.CASCADE, db_column='id_login', related_name='historial_sesiones')
    ip_origen = models.GenericIPAddressField()
    dispositivo_navegador = models.CharField(max_length=255)
    resultado = models.CharField(max_length=10, choices=RESULTADO_CHOICES)
    fecha_conexion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_historial_sesiones'
        verbose_name = 'Historial de sesión'
        verbose_name_plural = 'Historial de sesiones'


class HistorialBloqueosCuenta(models.Model):
    SOLICITADO_POR_CHOICES = [
        ('SISTEMA', 'Sistema (automático)'),
        ('ADMIN', 'Administrador'),
        ('USUARIO', 'Usuario'),
    ]

    id_historial_bloqueo = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario', related_name='bloqueos')
    motivo_bloqueo = models.CharField(max_length=255)
    solicitado_por = models.CharField(max_length=10, choices=SOLICITADO_POR_CHOICES)
    fecha_inicio_bloqueo = models.DateTimeField(auto_now_add=True)
    fecha_fin_bloqueo = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'tbl_historial_bloqueos_cuenta'
        verbose_name = 'Bloqueo de cuenta'
        verbose_name_plural = 'Bloqueos de cuenta'


class IntentoLogin(models.Model):
    """Registro de intentos de acceso (éxito/fallo) por IP, usado para mitigar
    fuerza bruta y ataques de denegación de servicio a nivel de aplicación."""
    id_intento = models.BigAutoField(primary_key=True)
    id_sistema_us = models.CharField(max_length=50, blank=True, null=True)
    ip_origen = models.GenericIPAddressField()
    exitoso = models.BooleanField(default=False)
    fecha_intento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_intento_login'
        verbose_name = 'Intento de login'
        verbose_name_plural = 'Intentos de login'
        indexes = [
            models.Index(fields=['ip_origen', 'fecha_intento']),
            models.Index(fields=['id_sistema_us', 'fecha_intento']),
        ]
