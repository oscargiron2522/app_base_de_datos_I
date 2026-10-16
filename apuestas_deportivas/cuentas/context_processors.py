from .models import Login


def sesion_actual(request):
    """Expone datos de la sesión (login actual) a todos los templates."""
    id_login = request.session.get('id_login')
    tipo_usuario = request.session.get('tipo_usuario')
    nombre_sesion = request.session.get('nombre_sesion')
    return {
        'sesion_id_login': id_login,
        'sesion_tipo_usuario': tipo_usuario,
        'sesion_nombre': nombre_sesion,
        'sesion_activa': id_login is not None,
    }
