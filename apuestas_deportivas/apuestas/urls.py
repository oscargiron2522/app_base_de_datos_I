from django.urls import path
from . import views

app_name = 'apuestas'

urlpatterns = [
    # Panel de usuario
    path('panel-usuario/', views.panel_usuario_inicio, name='panel_usuario_inicio'),
    path('panel-usuario/crear-boleto/', views.crear_boleto, name='crear_boleto'),
    path('panel-usuario/mis-boletos/', views.mis_boletos, name='mis_boletos'),

    # Panel administrativo
    path('panel-administrativo/', views.panel_admin_inicio, name='panel_admin_inicio'),
    path('panel-administrativo/eventos/', views.admin_eventos, name='admin_eventos'),
    path('panel-administrativo/eventos/<int:id_evento>/mercados/', views.admin_mercados_evento, name='admin_mercados_evento'),
    path('panel-administrativo/opciones/<int:id_opcion>/actualizar-cuota/', views.admin_actualizar_cuota, name='admin_actualizar_cuota'),
    path('panel-administrativo/eventos/<int:id_evento>/liquidar/', views.admin_liquidar_evento, name='admin_liquidar_evento'),
]
