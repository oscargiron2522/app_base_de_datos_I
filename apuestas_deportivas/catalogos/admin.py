from django.contrib import admin
from .models import Pais, Departamento, Municipio, Estado, Deporte, Liga, EquipoAtleta, TipoMercado, MetodoPago

for modelo in [Pais, Departamento, Municipio, Estado, Deporte, Liga, EquipoAtleta, TipoMercado, MetodoPago]:
    admin.site.register(modelo)
