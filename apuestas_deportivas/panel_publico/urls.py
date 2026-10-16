from django.urls import path
from . import views

app_name = 'panel_publico'

urlpatterns = [
    path('', views.inicio, name='inicio'),
]
