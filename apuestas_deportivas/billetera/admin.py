from django.contrib import admin
from .models import Billetera, Transaccion, CuentaBancariaUsuario, SolicitudRetiro, HistorialSaldoBilletera

for modelo in [Billetera, Transaccion, CuentaBancariaUsuario, SolicitudRetiro, HistorialSaldoBilletera]:
    admin.site.register(modelo)
