import re
from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from .models import Usuario, Login, PreguntaSeguridad

PATRON_TELEFONO = re.compile(r'^[0-9+\-\s]{8,20}$')


class RegistroUsuarioForm(forms.Form):
    primer_nombre_us = forms.CharField(max_length=80, label='Primer nombre')
    segundo_nombre_us = forms.CharField(max_length=80, label='Segundo nombre', required=False)
    primer_apellido_us = forms.CharField(max_length=80, label='Primer apellido')
    segundo_apellido_us = forms.CharField(max_length=80, label='Segundo apellido', required=False)
    apellido_casada_us = forms.CharField(max_length=80, label='Apellido de casada(o)', required=False)
    fecha_nacimiento_us = forms.DateField(label='Fecha de nacimiento', widget=forms.DateInput(attrs={'type': 'date'}))
    id_departamento_us = forms.IntegerField(label='Departamento')
    id_municipio_us = forms.IntegerField(label='Municipio')
    direccion_us = forms.CharField(max_length=255, label='Dirección')
    correo_us = forms.EmailField(label='Correo electrónico')
    telefono_us = forms.CharField(max_length=20, label='Teléfono')

    nombre_usuario = forms.CharField(max_length=100, label='Nombre de usuario')
    contrasena_usuario = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Contraseña')
    contrasena_confirmacion = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    pregunta_seguridad = forms.ModelChoiceField(queryset=PreguntaSeguridad.objects.all(), label='Pregunta de seguridad')
    respuesta_seguridad = forms.CharField(max_length=150, label='Respuesta')

    def clean_fecha_nacimiento_us(self):
        fecha = self.cleaned_data['fecha_nacimiento_us']
        edad = (date.today() - fecha).days // 365
        if edad < 18:
            raise ValidationError('Debes ser mayor de edad (18 años) para registrarte.')
        if fecha > date.today():
            raise ValidationError('La fecha de nacimiento no es válida.')
        return fecha

    def clean_telefono_us(self):
        telefono = self.cleaned_data['telefono_us']
        if not PATRON_TELEFONO.match(telefono):
            raise ValidationError('Formato de teléfono inválido.')
        return telefono

    def clean_correo_us(self):
        correo = self.cleaned_data['correo_us'].lower().strip()
        if Usuario.objects.filter(correo_us__iexact=correo).exists():
            raise ValidationError('Ya existe una cuenta registrada con este correo.')
        return correo

    def clean_nombre_usuario(self):
        nombre = self.cleaned_data['nombre_usuario'].strip()
        if Login.objects.filter(nombre_usuario__iexact=nombre).exists():
            raise ValidationError('El nombre de usuario ya está en uso.')
        if not re.match(r'^[A-Za-z0-9_.]{4,50}$', nombre):
            raise ValidationError('El usuario solo puede contener letras, números, punto y guion bajo (4-50 caracteres).')
        return nombre

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('contrasena_usuario')
        p2 = cleaned.get('contrasena_confirmacion')
        if p1 and p2 and p1 != p2:
            self.add_error('contrasena_confirmacion', 'Las contraseñas no coinciden.')
        return cleaned


class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(max_length=100, label='Usuario')
    contrasena_usuario = forms.CharField(widget=forms.PasswordInput, label='Contraseña')


class SolicitarRecuperacionForm(forms.Form):
    nombre_usuario = forms.CharField(max_length=100, label='Usuario')
    correo_registrado = forms.EmailField(label='Correo registrado')


class ResponderPreguntaForm(forms.Form):
    respuesta_seguridad = forms.CharField(max_length=150, label='Respuesta a tu pregunta de seguridad')


class NuevaContrasenaForm(forms.Form):
    contrasena_nueva = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Nueva contraseña')
    contrasena_confirmacion = forms.CharField(widget=forms.PasswordInput, label='Confirmar nueva contraseña')

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('contrasena_nueva')
        p2 = cleaned.get('contrasena_confirmacion')
        if p1 and p2 and p1 != p2:
            self.add_error('contrasena_confirmacion', 'Las contraseñas no coinciden.')
        return cleaned
