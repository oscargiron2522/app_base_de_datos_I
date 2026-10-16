from django.shortcuts import redirect
from django.contrib import messages


class ControlAccesoMiddleware:
    """Segunda capa de control de acceso por prefijo de URL, además de los
    decoradores usados en cada vista. Evita que, por descuido, una vista
    administrativa nueva quede expuesta sin protección."""

    PREFIJOS_ADMIN = ('/panel-administrativo/',)
    PREFIJOS_USUARIO = ('/panel-usuario/',)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tipo_usuario = request.session.get('tipo_usuario')
        ruta = request.path

        if ruta.startswith(self.PREFIJOS_ADMIN) and tipo_usuario not in ('ADMIN', 'SUPER_ADMIN'):
            messages.warning(request, 'Debes iniciar sesión como administrador.')
            return redirect('cuentas:login_admin')

        if ruta.startswith(self.PREFIJOS_USUARIO) and tipo_usuario != 'USUARIO':
            messages.warning(request, 'Debes iniciar sesión para acceder a tu panel.')
            return redirect('cuentas:login_usuario')

        return self.get_response(request)
