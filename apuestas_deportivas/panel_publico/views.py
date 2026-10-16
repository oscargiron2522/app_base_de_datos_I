from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from apuestas.models import Evento


def inicio(request):
    ahora = timezone.now()
    hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = hoy_inicio + timedelta(days=1)
    ayer_inicio = hoy_inicio - timedelta(days=1)

    eventos_hoy = (Evento.objects
                   .filter(fecha_inicio__gte=hoy_inicio, fecha_inicio__lt=hoy_fin)
                   .select_related('id_liga', 'id_equipo_local', 'id_equipo_visitante')
                   .prefetch_related('mercados__id_tipo_mercado', 'mercados__opciones')
                   .order_by('fecha_inicio'))

    eventos_ayer = (Evento.objects
                    .filter(fecha_inicio__gte=ayer_inicio, fecha_inicio__lt=hoy_inicio)
                    .select_related('id_liga', 'id_equipo_local', 'id_equipo_visitante', 'resultado')
                    .order_by('fecha_inicio'))

    return render(request, 'panel_publico/inicio.html', {
        'eventos_hoy': eventos_hoy,
        'eventos_ayer': eventos_ayer,
    })
