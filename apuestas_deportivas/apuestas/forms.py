from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal


class MontoApuestaForm(forms.Form):
    monto_apostado = forms.DecimalField(max_digits=14, decimal_places=2, label='Monto a apostar')
    opciones = forms.CharField(widget=forms.HiddenInput)  # lista de ids separados por coma

    def clean_monto_apostado(self):
        monto = self.cleaned_data['monto_apostado']
        if monto <= Decimal('0'):
            raise ValidationError('El monto apostado debe ser mayor a cero.')
        if monto > Decimal('999999.99'):
            raise ValidationError('El monto excede el límite permitido.')
        return monto

    def clean_opciones(self):
        crudo = self.cleaned_data['opciones']
        try:
            ids = [int(x) for x in crudo.split(',') if x.strip() != '']
        except ValueError:
            raise ValidationError('Selección de opciones inválida.')
        if not ids:
            raise ValidationError('Debes seleccionar al menos una opción de apuesta.')
        if len(ids) != len(set(ids)):
            raise ValidationError('No puedes repetir la misma opción en un boleto.')
        return ids


class EventoForm(forms.Form):
    id_liga = forms.IntegerField(label='Liga')
    id_equipo_local = forms.IntegerField(label='Equipo/atleta local')
    id_equipo_visitante = forms.IntegerField(label='Equipo/atleta visitante')
    fecha_inicio = forms.DateTimeField(label='Fecha y hora', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('id_equipo_local') and cleaned.get('id_equipo_visitante'):
            if cleaned['id_equipo_local'] == cleaned['id_equipo_visitante']:
                raise ValidationError('El equipo local y visitante no pueden ser el mismo.')
        return cleaned


class MercadoOpcionForm(forms.Form):
    id_tipo_mercado = forms.IntegerField(label='Tipo de mercado')
    descripcion_opcion = forms.CharField(max_length=150, label='Descripción de la opción')
    cuota_actual = forms.DecimalField(max_digits=6, decimal_places=2, label='Cuota')

    def clean_cuota_actual(self):
        cuota = self.cleaned_data['cuota_actual']
        if cuota <= Decimal('1.00'):
            raise ValidationError('La cuota debe ser mayor a 1.00.')
        return cuota


class ResultadoEventoForm(forms.Form):
    puntuacion_local = forms.IntegerField(min_value=0, label='Marcador local')
    puntuacion_visitante = forms.IntegerField(min_value=0, label='Marcador visitante')
    observaciones = forms.CharField(required=False, widget=forms.Textarea, label='Observaciones')

    def clean_puntuacion_local(self):
        valor = self.cleaned_data['puntuacion_local']
        if valor < 0:
            raise ValidationError('El marcador no puede ser negativo.')
        return valor

    def clean_puntuacion_visitante(self):
        valor = self.cleaned_data['puntuacion_visitante']
        if valor < 0:
            raise ValidationError('El marcador no puede ser negativo.')
        return valor
