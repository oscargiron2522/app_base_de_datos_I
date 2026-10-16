from django.urls import path
from . import views

app_name = 'cuentas'

urlpatterns = [
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('api/municipios/<int:id_departamento>/', views.api_municipios, name='api_municipios'),

    path('login/', views.login_usuario, name='login_usuario'),
    path('login-admin/', views.login_admin, name='login_admin'),
    path('logout/', views.logout_view, name='logout'),

    path('recuperar/', views.recuperar_password_solicitud, name='recuperar_solicitud'),
    path('recuperar/pregunta/', views.recuperar_password_pregunta, name='recuperar_pregunta'),
    path('recuperar/confirmar/<uuid:token>/', views.recuperar_password_confirmar, name='recuperar_confirmar'),
]
