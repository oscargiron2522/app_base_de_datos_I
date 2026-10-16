from django.contrib import admin
from .models import (
    Login, LoginLog, Usuario, Administrador, SuperAdministrador,
    PreguntaSeguridad, UsuarioPreguntaSeguridad, RecuperacionPassword,
    AdminLog, HistorialSesiones, HistorialBloqueosCuenta, IntentoLogin,
)

for modelo in [Login, LoginLog, Usuario, Administrador, SuperAdministrador,
               PreguntaSeguridad, UsuarioPreguntaSeguridad, RecuperacionPassword,
               AdminLog, HistorialSesiones, HistorialBloqueosCuenta, IntentoLogin]:
    admin.site.register(modelo)
