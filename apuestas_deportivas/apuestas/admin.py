from django.contrib import admin
from .models import (
    Evento, ResultadoEvento, MercadoEvento, OpcionApuesta, PromocionCuota,
    Boleto, DetalleBoleto, HistorialCuotas, HistorialEstadoBoleto,
    HistorialCambiosEvento, HistorialJugadorResumen,
)

for modelo in [Evento, ResultadoEvento, MercadoEvento, OpcionApuesta, PromocionCuota,
               Boleto, DetalleBoleto, HistorialCuotas, HistorialEstadoBoleto,
               HistorialCambiosEvento, HistorialJugadorResumen]:
    admin.site.register(modelo)
