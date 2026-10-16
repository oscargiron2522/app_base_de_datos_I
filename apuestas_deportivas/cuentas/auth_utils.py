"""
Utilidades de autenticación basadas en el modelo propio tbl_login (no se usa
django.contrib.auth.User, ya que el diagrama del sistema define su propio
esquema de login / usuario / administrador / super administrador).
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from .models import Login


def iniciar_sesion(request, login_obj: Login, nombre_mostrar: str):
    request.session.flush()
    request.session['id_login'] = login_obj.id_login
    request.session['tipo_usuario'] = login_obj.tipo_usuario
    request.session['nombre_sesion'] = nombre_mostrar
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)


def cerrar_sesion(request):
    request.session.flush()


def obtener_login_actual(request):
    id_login = request.session.get('id_login')
    if not id_login:
        return None
    return Login.objects.filter(id_login=id_login).first()


def cuenta_bloqueada(login_obj: Login) -> bool:
    return bool(login_obj.bloqueado_hasta and login_obj.bloqueado_hasta > timezone.now())


def registrar_intento_fallido(login_obj: Login):
    login_obj.intentos_fallidos += 1
    if login_obj.intentos_fallidos >= settings.SEGURIDAD_MAX_INTENTOS_LOGIN:
        login_obj.bloqueado_hasta = timezone.now() + timedelta(minutes=settings.SEGURIDAD_MINUTOS_BLOQUEO_LOGIN)
        login_obj.intentos_fallidos = 0
    login_obj.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])


def limpiar_intentos_fallidos(login_obj: Login):
    if login_obj.intentos_fallidos or login_obj.bloqueado_hasta:
        login_obj.intentos_fallidos = 0
        login_obj.bloqueado_hasta = None
        login_obj.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])


def requiere_sesion(tipos_permitidos):
    """Decorador para proteger vistas según el tipo de login en sesión.
    tipos_permitidos: lista con combinación de 'USUARIO', 'ADMIN', 'SUPER_ADMIN'.
    """
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            tipo_usuario = request.session.get('tipo_usuario')
            if not tipo_usuario or tipo_usuario not in tipos_permitidos:
                messages.warning(request, 'Debes iniciar sesión para acceder a esta sección.')
                if 'ADMIN' in tipos_permitidos or 'SUPER_ADMIN' in tipos_permitidos:
                    return redirect('cuentas:login_admin')
                return redirect('cuentas:login_usuario')
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
