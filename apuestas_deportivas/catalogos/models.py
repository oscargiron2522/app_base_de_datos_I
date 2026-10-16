from django.db import models


class Pais(models.Model):
    id_pais = models.AutoField(primary_key=True)
    nombre_pais = models.CharField(max_length=100)
    codigo_iso = models.CharField(max_length=5)

    class Meta:
        db_table = 'tbl_pais'
        verbose_name = 'País'
        verbose_name_plural = 'Países'

    def __str__(self):
        return self.nombre_pais


class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    id_pais = models.ForeignKey(Pais, on_delete=models.PROTECT, db_column='id_pais', related_name='departamentos')
    nombre_departamento = models.CharField(max_length=100)
    comentario_departamento = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'tbl_departamento'
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'

    def __str__(self):
        return self.nombre_departamento


class Municipio(models.Model):
    id_municipio = models.AutoField(primary_key=True)
    id_departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, db_column='id_departamento', related_name='municipios')
    nombre_municipio = models.CharField(max_length=100)
    comentario_municipio = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'tbl_municipio'
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'

    def __str__(self):
        return self.nombre_municipio


class Estado(models.Model):
    """Catálogo genérico de estados (activo, inactivo, bloqueado, suspendido, etc.)."""
    id_estado = models.AutoField(primary_key=True)
    nombre_estado = models.CharField(max_length=50)
    comentario_estado = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'tbl_estado'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.nombre_estado


class Deporte(models.Model):
    id_deporte = models.AutoField(primary_key=True)
    nombre_deporte = models.CharField(max_length=100)
    id_estado = models.ForeignKey(Estado, on_delete=models.PROTECT, db_column='id_estado', related_name='deportes')

    class Meta:
        db_table = 'tbl_deporte'
        verbose_name = 'Deporte'
        verbose_name_plural = 'Deportes'

    def __str__(self):
        return self.nombre_deporte


class Liga(models.Model):
    id_liga = models.AutoField(primary_key=True)
    id_deporte = models.ForeignKey(Deporte, on_delete=models.PROTECT, db_column='id_deporte', related_name='ligas')
    id_pais = models.ForeignKey(Pais, on_delete=models.PROTECT, db_column='id_pais', related_name='ligas')
    nombre_liga = models.CharField(max_length=150)

    class Meta:
        db_table = 'tbl_liga'
        verbose_name = 'Liga'
        verbose_name_plural = 'Ligas'

    def __str__(self):
        return self.nombre_liga


class EquipoAtleta(models.Model):
    id_equipo = models.AutoField(primary_key=True)
    nombre_equipo = models.CharField(max_length=150)
    id_deporte = models.ForeignKey(Deporte, on_delete=models.PROTECT, db_column='id_deporte', related_name='equipos')

    class Meta:
        db_table = 'tbl_equipo_atleta'
        verbose_name = 'Equipo/Atleta'
        verbose_name_plural = 'Equipos/Atletas'

    def __str__(self):
        return self.nombre_equipo


class TipoMercado(models.Model):
    id_tipo_mercado = models.AutoField(primary_key=True)
    nombre_mercado = models.CharField(max_length=100)

    class Meta:
        db_table = 'tbl_tipo_mercado'
        verbose_name = 'Tipo de mercado'
        verbose_name_plural = 'Tipos de mercado'

    def __str__(self):
        return self.nombre_mercado


class MetodoPago(models.Model):
    id_metodo_pago = models.AutoField(primary_key=True)
    nombre_metodo = models.CharField(max_length=100)
    comision_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'tbl_metodo_pago'
        verbose_name = 'Método de pago'
        verbose_name_plural = 'Métodos de pago'

    def __str__(self):
        return self.nombre_metodo
