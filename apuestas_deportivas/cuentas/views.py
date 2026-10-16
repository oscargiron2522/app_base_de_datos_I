from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.db import transaction

from catalogos.models import Estado, Departamento, Municipio
from .models import (
    Login, Usuario, Administrador, SuperAdministrador, HistorialSesiones,
    RecuperacionPassword, UsuarioPreguntaSeguridad, PreguntaSeguridad, IntentoLogin,
)
from .forms import (
    RegistroUsuarioForm, LoginForm, SolicitarRecuperacionForm,
    ResponderPreguntaForm, NuevaContrasenaForm,
)
from .auth_utils import (
    iniciar_sesion, cerrar_sesion, cuenta_bloqueada,
    registrar_intento_fallido, limpiar_intentos_fallidos, requiere_sesion,
)
from billetera.models import Billetera


def _obtener_ip(request):
    xf = request.META.get('HTTP_X_FORWARDED_FOR')
    return xf.split(',')[0].strip() if xf else request.META.get('REMOTE_ADDR', '0.0.0.0')


def _registrar_historial_sesion(login_obj, request, resultado):
    HistorialSesiones.objects.create(
        id_login=login_obj,
        ip_origen=_obtener_ip(request),
        dispositivo_navegador=request.META.get('HTTP_USER_AGENT', 'desconocido')[:255],
        resultado=resultado,
    )


# --------------------------------------------------------------------------
# Registro de usuarios finales
# --------------------------------------------------------------------------
def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                estado_activo, _ = Estado.objects.get_or_create(
                    nombre_estado='ACTIVO', defaults={'comentario_estado': 'Registro activo'})

                login_obj = Login(
                    id_sistema_us=data['correo_us'],
                    nombre_usuario=data['nombre_usuario'],
                    tipo_usuario='USUARIO',
                )
                login_obj.set_password(data['contrasena_usuario'])
                login_obj.save()

                usuario = Usuario.objects.create(
                    id_login=login_obj,
                    primer_nombre_us=data['primer_nombre_us'],
                    segundo_nombre_us=data.get('segundo_nombre_us') or None,
                    primer_apellido_us=data['primer_apellido_us'],
                    segundo_apellido_us=data.get('segundo_apellido_us') or None,
                    apellido_casada_us=data.get('apellido_casada_us') or None,
                    fecha_nacimiento_us=data['fecha_nacimiento_us'],
                    id_departamento_us_id=data['id_departamento_us'],
                    id_municipio_us_id=data['id_municipio_us'],
                    direccion_us=data['direccion_us'],
                    correo_us=data['correo_us'],
                    telefono_us=data['telefono_us'],
                    id_estado=estado_activo,
                )

                pregunta_resp = UsuarioPreguntaSeguridad(
                    id_login=login_obj, id_pregunta=data['pregunta_seguridad'])
                pregunta_resp.set_respuesta(data['respuesta_seguridad'])
                pregunta_resp.save()

                estado_billetera, _ = Estado.objects.get_or_create(
                    nombre_estado='ACTIVA', defaults={'comentario_estado': 'Billetera activa'})
                Billetera.objects.create(id_usuario=usuario, id_estado=estado_billetera)

            messages.success(request, 'Registro exitoso. Ya puedes iniciar sesión.')
            return redirect('cuentas:login_usuario')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'cuentas/registro.html', {
        'form': form,
        'departamentos': Departamento.objects.all(),
    })


def api_municipios(request, id_departamento):
    municipios = Municipio.objects.filter(id_departamento_id=id_departamento).values('id_municipio', 'nombre_municipio')
    from django.http import JsonResponse
    return JsonResponse(list(municipios), safe=False)


# --------------------------------------------------------------------------
# Login (usuario / administrador comparten la misma lógica de credenciales)
# --------------------------------------------------------------------------
def _procesar_login(request, tipos_permitidos, plantilla, redireccion_exito):
    if request.session.get('id_login'):
        return redirect(redireccion_exito)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        ip = _obtener_ip(request)
        if form.is_valid():
            nombre_usuario = form.cleaned_data['nombre_usuario']
            contrasena = form.cleaned_data['contrasena_usuario']
            login_obj = Login.objects.filter(nombre_usuario=nombre_usuario, tipo_usuario__in=tipos_permitidos).first()

            exitoso = False
            if login_obj and cuenta_bloqueada(login_obj):
                messages.error(request, 'Tu cuenta está temporalmente bloqueada por múltiples intentos fallidos. Intenta más tarde.')
            elif login_obj and login_obj.check_password(contrasena):
                limpiar_intentos_fallidos(login_obj)
                nombre_mostrar = nombre_usuario
                if login_obj.tipo_usuario == 'USUARIO' and hasattr(login_obj, 'usuario'):
                    nombre_mostrar = login_obj.usuario.nombre_completo()
                elif login_obj.tipo_usuario in ('ADMIN',) and hasattr(login_obj, 'administrador'):
                    nombre_mostrar = f'{login_obj.administrador.primer_nombre_admin} {login_obj.administrador.primer_apellido_admin}'
                elif login_obj.tipo_usuario == 'SUPER_ADMIN' and hasattr(login_obj, 'super_administrador'):
                    nombre_mostrar = login_obj.super_administrador.nombre_completo

                iniciar_sesion(request, login_obj, nombre_mostrar)
                exitoso = True
            else:
                if login_obj:
                    registrar_intento_fallido(login_obj)
                messages.error(request, 'Usuario o contraseña incorrectos.')

            IntentoLogin.objects.create(id_sistema_us=nombre_usuario, ip_origen=ip, exitoso=exitoso)
            if login_obj:
                _registrar_historial_sesion(login_obj, request, 'EXITOSO' if exitoso else 'FALLIDO')

            if exitoso:
                return redirect(redireccion_exito)
    else:
        form = LoginForm()

    return render(request, plantilla, {'form': form})


def login_usuario(request):
    return _procesar_login(request, ['USUARIO'], 'cuentas/login_usuario.html', 'apuestas:panel_usuario_inicio')


def login_admin(request):
    return _procesar_login(request, ['ADMIN', 'SUPER_ADMIN'], 'cuentas/login_admin.html', 'apuestas:panel_admin_inicio')


def logout_view(request):
    cerrar_sesion(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('panel_publico:inicio')


# --------------------------------------------------------------------------
# Recuperación de contraseña (usuario + pregunta de seguridad + correo)
# --------------------------------------------------------------------------
def recuperar_password_solicitud(request):
    if request.method == 'POST':
        form = SolicitarRecuperacionForm(request.POST)
        if form.is_valid():
            nombre_usuario = form.cleaned_data['nombre_usuario']
            correo = form.cleaned_data['correo_registrado'].lower().strip()

            login_obj = Login.objects.filter(nombre_usuario=nombre_usuario).first()
            correo_valido = False
            if login_obj:
                if login_obj.tipo_usuario == 'USUARIO' and hasattr(login_obj, 'usuario'):
                    correo_valido = login_obj.usuario.correo_us.lower() == correo
                elif login_obj.tipo_usuario == 'ADMIN' and hasattr(login_obj, 'administrador'):
                    correo_valido = login_obj.administrador.correo_corporativo.lower() == correo
                elif login_obj.tipo_usuario == 'SUPER_ADMIN' and hasattr(login_obj, 'super_administrador'):
                    correo_valido = login_obj.super_administrador.correo_maestro.lower() == correo

            # Respuesta neutra siempre, para no revelar si el usuario existe.
            messages.info(request, 'Si los datos son correctos, se enviaron instrucciones a tu correo.')

            if login_obj and correo_valido:
                request.session['recuperacion_id_login'] = login_obj.id_login
                return redirect('cuentas:recuperar_pregunta')
            return redirect('cuentas:login_usuario')
    else:
        form = SolicitarRecuperacionForm()
    return render(request, 'cuentas/recuperar_solicitud.html', {'form': form})


def recuperar_password_pregunta(request):
    id_login = request.session.get('recuperacion_id_login')
    if not id_login:
        return redirect('cuentas:recuperar_solicitud')
    login_obj = get_object_or_404(Login, id_login=id_login)
    pregunta_resp = UsuarioPreguntaSeguridad.objects.filter(id_login=login_obj).first()

    if request.method == 'POST':
        form = ResponderPreguntaForm(request.POST)
        if form.is_valid():
            if pregunta_resp and pregunta_resp.check_respuesta(form.cleaned_data['respuesta_seguridad']):
                token_obj = RecuperacionPassword.objects.create(
                    id_login=login_obj,
                    fecha_expiracion=timezone.now() + timedelta(minutes=settings.SEGURIDAD_MINUTOS_VIGENCIA_TOKEN_RESET),
                    ip_solicitud=_obtener_ip(request),
                )
                enlace = request.build_absolute_uri(
                    reverse('cuentas:recuperar_confirmar', args=[str(token_obj.token)]))

                correo_destino = None
                if hasattr(login_obj, 'usuario'):
                    correo_destino = login_obj.usuario.correo_us
                elif hasattr(login_obj, 'administrador'):
                    correo_destino = login_obj.administrador.correo_corporativo
                elif hasattr(login_obj, 'super_administrador'):
                    correo_destino = login_obj.super_administrador.correo_maestro

                send_mail(
                    subject='Recuperación de contraseña - Apuestas Deportivas',
                    message=(
                        f'Hola,\n\nRecibimos una solicitud para restablecer tu contraseña.\n'
                        f'Ingresa al siguiente enlace (válido por {settings.SEGURIDAD_MINUTOS_VIGENCIA_TOKEN_RESET} minutos):\n\n'
                        f'{enlace}\n\nSi no solicitaste este cambio, ignora este correo.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[correo_destino] if correo_destino else [],
                    fail_silently=True,
                )
                del request.session['recuperacion_id_login']
                messages.success(request, 'Respuesta correcta. Se envió un enlace de confirmación a tu correo.')
                return redirect('cuentas:login_usuario')
            messages.error(request, 'La respuesta de seguridad no es correcta.')
    else:
        form = ResponderPreguntaForm()

    return render(request, 'cuentas/recuperar_pregunta.html', {
        'form': form,
        'pregunta': pregunta_resp.id_pregunta.texto_pregunta if pregunta_resp else None,
    })


def recuperar_password_confirmar(request, token):
    token_obj = get_object_or_404(RecuperacionPassword, token=token)
    if token_obj.usado or token_obj.fecha_expiracion < timezone.now():
        messages.error(request, 'El enlace de recuperación no es válido o ha expirado.')
        return redirect('cuentas:recuperar_solicitud')

    if request.method == 'POST':
        form = NuevaContrasenaForm(request.POST)
        if form.is_valid():
            login_obj = token_obj.id_login
            login_obj.set_password(form.cleaned_data['contrasena_nueva'])
            login_obj.ultimo_cambio_password = timezone.now()
            login_obj.save()
            token_obj.usado = True
            token_obj.save(update_fields=['usado'])
            messages.success(request, 'Contraseña actualizada correctamente. Ya puedes iniciar sesión.')
            return redirect('cuentas:login_usuario')
    else:
        form = NuevaContrasenaForm()

    return render(request, 'cuentas/recuperar_confirmar.html', {'form': form})
