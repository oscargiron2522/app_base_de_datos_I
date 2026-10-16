from django.urls import path
from . import views

app_name = 'billetera'

urlpatterns = [
    path('panel-usuario/deposito/', views.deposito, name='deposito'),
    path('panel-usuario/cuentas-bancarias/', views.mis_cuentas_bancarias, name='mis_cuentas_bancarias'),
    path('panel-usuario/retiro/', views.solicitar_retiro, name='solicitar_retiro'),
    path('panel-administrativo/retiros/', views.admin_solicitudes_retiro, name='admin_solicitudes_retiro'),
]
