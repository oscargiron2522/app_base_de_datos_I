from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from cuentas.auth_utils import requiere_sesion, obtener_login_actual
from cuentas.models import Administrador, Usuario
from catalogos.models import Liga, EquipoAtleta, TipoMercado, Deporte, Estado
from billetera.models import Billetera, HistorialSaldoBilletera
from .models import (
    Evento, MercadoEvento, OpcionApuesta, Boleto, DetalleBoleto,
    ResultadoEvento, HistorialCuotas, HistorialEstadoBoleto, HistorialCambiosEvento,
)
from .forms import MontoApuestaForm, EventoForm, MercadoOpcionForm, ResultadoEventoForm


# ==========================================================================
# PANEL DE USUARIO
# ==========================================================================
@requiere_sesion(['USUARIO'])
def panel_usuario_inicio(request):
    login_obj = obtener_login_actual(request)
    usuario = login_obj.usuario
    billetera = usuario.billetera

    eventos = (Evento.objects
               .filter(estado_evento='PROGRAMADO', fecha_inicio__gte=timezone.now())
               .select_related('id_liga', 'id_equipo_local', 'id_equipo_visitante')
               .prefetch_related('mercados__id_tipo_mercado', 'mercados__opciones')
               .order_by('fecha_inicio')[:30])

    return render(request, 'apuestas/panel_usuario_inicio.html', {
        'usuario': usuario,
        'billetera': billetera,
        'eventos': eventos,
    })


@requiere_sesion(['USUARIO'])
def crear_boleto(request):
    if request.method != 'POST':
        return redirect('apuestas:panel_usuario_inicio')

    login_obj = obtener_login_actual(request)
    usuario = login_obj.usuario
    billetera = usuario.billetera

    form = MontoApuestaForm(request.POST)
    if not form.is_valid():
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        return redirect('apuestas:panel_usuario_inicio')

    monto = form.cleaned_data['monto_apostado']
    ids_opciones = form.cleaned_data['opciones']

    opciones = list(OpcionApuesta.objects.select_related('id_mercado_evento__id_evento').filter(id_opcion__in=ids_opciones))
    if len(opciones) != len(ids_opciones):
        messages.error(request, 'Alguna de las opciones seleccionadas ya no está disponible.')
        return redirect('apuestas:panel_usuario_inicio')

    for opcion in opciones:
        if opcion.id_mercado_evento.estado_mercado != 'ABIERTO':
            messages.error(request, 'Uno de los mercados seleccionados ya está cerrado.')
            return redirect('apuestas:panel_usuario_inicio')
        if opcion.id_mercado_evento.id_evento.estado_evento not in ('PROGRAMADO',):
            messages.error(request, 'Uno de los eventos seleccionados ya no admite apuestas.')
            return redirect('apuestas:panel_usuario_inicio')

    cuota_total = Decimal('1.00')
    for opcion in opciones:
        cuota_total *= opcion.cuota_actual
    cuota_total = cuota_total.quantize(Decimal('0.01'))
    ganancia_potencial = (monto * cuota_total).quantize(Decimal('0.01'))

    try:
        with transaction.atomic():
            billetera_bloqueada = Billetera.objects.select_for_update().get(pk=billetera.pk)
            if monto > billetera_bloqueada.saldo_disponible:
                messages.error(request, 'Saldo disponible insuficiente para realizar esta apuesta.')
                return redirect('apuestas:panel_usuario_inicio')

            saldo_anterior = billetera_bloqueada.saldo_disponible
            billetera_bloqueada.saldo_disponible -= monto
            billetera_bloqueada.saldo_retenido += monto
            billetera_bloqueada.save(update_fields=['saldo_disponible', 'saldo_retenido'])

            HistorialSaldoBilletera.objects.create(
                id_billetera=billetera_bloqueada,
                saldo_anterior=saldo_anterior,
                saldo_nuevo=billetera_bloqueada.saldo_disponible,
                monto_movimiento=monto,
                tipo_operacion='DEBITO_APUESTA',
            )

            boleto = Boleto.objects.create(
                id_billetera=billetera_bloqueada,
                monto_apostado=monto,
                cuota_total=cuota_total,
                ganancia_potencial=ganancia_potencial,
                estado_boleto='PENDIENTE',
            )
            for opcion in opciones:
                DetalleBoleto.objects.create(id_boleto=boleto, id_opcion=opcion, cuota_momento=opcion.cuota_actual)

        messages.success(request, f'Boleto #{boleto.id_boleto} creado con éxito. Ganancia potencial: Q{ganancia_potencial}')
    except Exception:
        messages.error(request, 'Ocurrió un error al procesar tu apuesta. Intenta nuevamente.')

    return redirect('apuestas:panel_usuario_inicio')


@requiere_sesion(['USUARIO'])
def mis_boletos(request):
    login_obj = obtener_login_actual(request)
    boletos = (Boleto.objects
               .filter(id_billetera__id_usuario=login_obj.usuario)
               .prefetch_related('detalles__id_opcion__id_mercado_evento__id_evento')
               .order_by('-fecha_emision'))
    return render(request, 'apuestas/mis_boletos.html', {'boletos': boletos})


# ==========================================================================
# PANEL ADMINISTRATIVO
# ==========================================================================
def _rol_admin_actual(request):
    login_obj = obtener_login_actual(request)
    if login_obj.tipo_usuario == 'SUPER_ADMIN':
        return 'SUPER_ADMIN', login_obj
    if hasattr(login_obj, 'administrador'):
        return login_obj.administrador.rol_administrativo, login_obj
    return None, login_obj


@requiere_sesion(['ADMIN', 'SUPER_ADMIN'])
def panel_admin_inicio(request):
    rol, login_obj = _rol_admin_actual(request)
    contexto = {
        'rol': rol,
        'total_usuarios': Usuario.objects.count(),
        'total_eventos_programados': Evento.objects.filter(estado_evento='PROGRAMADO').count(),
        'total_boletos_pendientes': Boleto.objects.filter(estado_boleto='PENDIENTE').count(),
        'total_solicitudes_retiro': __import__('billetera.models', fromlist=['SolicitudRetiro']).SolicitudRetiro.objects.filter(estado_solicitud='PENDIENTE').count(),
    }
    return render(request, 'apuestas/panel_admin_inicio.html', contexto)


@requiere_sesion(['ADMIN', 'SUPER_ADMIN'])
def admin_eventos(request):
    rol, login_obj = _rol_admin_actual(request)
    if rol not in ('OPERADOR_EVENTOS', 'SUPER_ADMIN'):
        messages.error(request, 'No tienes permisos para gestionar eventos.')
        return redirect('apuestas:panel_admin_inicio')

    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            Evento.objects.create(
                id_liga_id=form.cleaned_data['id_liga'],
                id_equipo_local_id=form.cleaned_data['id_equipo_local'],
                id_equipo_visitante_id=form.cleaned_data['id_equipo_visitante'],
                fecha_inicio=form.cleaned_data['fecha_inicio'],
                estado_evento='PROGRAMADO',
            )
            messages.success(request, 'Evento creado correctamente.')
            return redirect('apuestas:admin_eventos')
        else:
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
    else:
        form = EventoForm()

    eventos = Evento.objects.select_related('id_liga', 'id_equipo_local', 'id_equipo_visitante').order_by('-fecha_inicio')[:100]
    return render(request, 'apuestas/admin_eventos.html', {
        'form': form, 'eventos': eventos,
        'ligas': Liga.objects.all(), 'equipos': EquipoAtleta.objects.all(),
    })


@requiere_sesion(['ADMIN', 'SUPER_ADMIN'])
def admin_mercados_evento(request, id_evento):
    rol, login_obj = _rol_admin_actual(request)
    if rol not in ('OPERADOR_EVENTOS', 'SUPER_ADMIN'):
        messages.error(request, 'No tienes permisos para gestionar mercados.')
        return redirect('apuestas:panel_admin_inicio')

    evento = get_object_or_404(Evento, pk=id_evento)

    if request.method == 'POST':
        form = MercadoOpcionForm(request.POST)
        if form.is_valid():
            mercado, _ = MercadoEvento.objects.get_or_create(
                id_evento=evento, id_tipo_mercado_id=form.cleaned_data['id_tipo_mercado'])
            OpcionApuesta.objects.create(
                id_mercado_evento=mercado,
                descripcion_opcion=form.cleaned_data['descripcion_opcion'],
                cuota_actual=form.cleaned_data['cuota_actual'],
            )
            messages.success(request, 'Mercado/opción agregada correctamente.')
            return redirect('apuestas:admin_mercados_evento', id_evento=id_evento)
        else:
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
    else:
        form = MercadoOpcionForm()

    mercados = evento.mercados.prefetch_related('opciones').select_related('id_tipo_mercado').all()
    return render(request, 'apuestas/admin_mercados_evento.html', {
        'evento': evento, 'form': form, 'mercados': mercados,
        'tipos_mercado': TipoMercado.objects.all(),
    })


@requiere_sesion(['ADMIN', 'SUPER_ADMIN'])
def admin_actualizar_cuota(request, id_opcion):
    rol, login_obj = _rol_admin_actual(request)
    opcion = get_object_or_404(OpcionApuesta, pk=id_opcion)
    if rol not in ('OPERADOR_EVENTOS', 'SUPER_ADMIN'):
        messages.error(request, 'No tienes permisos para modificar cuotas.')
        return redirect('apuestas:panel_admin_inicio')

    if request.method == 'POST':
        try:
            nueva_cuota = Decimal(request.POST.get('cuota_actual', '0'))
        except Exception:
            nueva_cuota = Decimal('0')
        if nueva_cuota <= Decimal('1.00'):
            messages.error(request, 'La cuota debe ser mayor a 1.00.')
        else:
            cuota_anterior = opcion.cuota_actual
            opcion.cuota_actual = nueva_cuota
            opcion.save(update_fields=['cuota_actual'])
            admin_obj = getattr(login_obj, 'administrador', None)
            HistorialCuotas.objects.create(
                id_opcion=opcion, cuota_anterior=cuota_anterior,
                cuota_nueva=nueva_cuota, id_admin=admin_obj,
            )
            messages.success(request, 'Cuota actualizada.')
    return redirect('apuestas:admin_mercados_evento', id_evento=opcion.id_mercado_evento.id_evento_id)


@requiere_sesion(['ADMIN', 'SUPER_ADMIN'])
def admin_liquidar_evento(request, id_evento):
    """Registra el resultado oficial de un evento, marca las opciones ganadoras
    y liquida automáticamente todos los boletos abiertos asociados."""
    rol, login_obj = _rol_admin_actual(request)
    if rol not in ('OPERADOR_EVENTOS', 'SUPER_ADMIN'):
        messages.error(request, 'No tienes permisos para liquidar eventos.')
        return redirect('apuestas:panel_admin_inicio')

    evento = get_object_or_404(Evento, pk=id_evento)

    if request.method == 'POST':
        form = ResultadoEventoForm(request.POST)
        ids_ganadoras = set(int(x) for x in request.POST.getlist('opciones_ganadoras'))
        if form.is_valid():
            with transaction.atomic():
                ResultadoEvento.objects.update_or_create(
                    id_evento=evento,
                    defaults={
                        'puntuacion_local': form.cleaned_data['puntuacion_local'],
                        'puntuacion_visitante': form.cleaned_data['puntuacion_visitante'],
                        'observaciones': form.cleaned_data.get('observaciones', ''),
                    },
                )
                estado_anterior = evento.estado_evento
                evento.estado_evento = 'FINALIZADO'
                evento.save(update_fields=['estado_evento'])
                HistorialCambiosEvento.objects.create(
                    id_evento=evento, estado_anterior=estado_anterior, estado_nuevo='FINALIZADO',
                    marcador_momento=f"{form.cleaned_data['puntuacion_local']}-{form.cleaned_data['puntuacion_visitante']}",
                )

                opciones_evento = OpcionApuesta.objects.filter(id_mercado_evento__id_evento=evento)
                for opcion in opciones_evento:
                    opcion.es_ganadora = opcion.id_opcion in ids_ganadoras
                opciones_evento_actualizadas = list(opciones_evento)
                for opcion in opciones_evento_actualizadas:
                    opcion.save(update_fields=['es_ganadora'])
                MercadoEvento.objects.filter(id_evento=evento).update(estado_mercado='LIQUIDADO')

                # Liquidación de boletos con al menos una selección de este evento.
                boletos_afectados = (Boleto.objects
                                      .filter(detalles__id_opcion__id_mercado_evento__id_evento=evento,
                                              estado_boleto='PENDIENTE')
                                      .distinct())

                for boleto in boletos_afectados:
                    detalles = list(boleto.detalles.select_related('id_opcion__id_mercado_evento__id_evento'))
                    eventos_boleto = {d.id_opcion.id_mercado_evento.id_evento_id for d in detalles}
                    # Solo se liquida si TODOS los eventos del boleto ya finalizaron.
                    if Evento.objects.filter(id_evento__in=eventos_boleto).exclude(estado_evento='FINALIZADO').exists():
                        continue

                    todas_ganadoras = all(d.id_opcion.es_ganadora for d in detalles)
                    estado_anterior_boleto = boleto.estado_boleto
                    billetera_bloqueada = Billetera.objects.select_for_update().get(pk=boleto.id_billetera_id)

                    if todas_ganadoras:
                        boleto.estado_boleto = 'GANADO'
                        saldo_anterior = billetera_bloqueada.saldo_disponible
                        billetera_bloqueada.saldo_retenido -= boleto.monto_apostado
                        billetera_bloqueada.saldo_disponible += boleto.ganancia_potencial
                        billetera_bloqueada.save(update_fields=['saldo_disponible', 'saldo_retenido'])
                        HistorialSaldoBilletera.objects.create(
                            id_billetera=billetera_bloqueada, saldo_anterior=saldo_anterior,
                            saldo_nuevo=billetera_bloqueada.saldo_disponible,
                            monto_movimiento=boleto.ganancia_potencial, tipo_operacion='CREDITO_PREMIO',
                        )
                    else:
                        boleto.estado_boleto = 'PERDIDO'
                        billetera_bloqueada.saldo_retenido -= boleto.monto_apostado
                        billetera_bloqueada.save(update_fields=['saldo_retenido'])

                    boleto.save(update_fields=['estado_boleto'])
                    HistorialEstadoBoleto.objects.create(
                        id_boleto=boleto, estado_anterior=estado_anterior_boleto,
                        estado_nuevo=boleto.estado_boleto, motivo_cambio='Liquidación automática de evento',
                    )

            messages.success(request, 'Evento liquidado y boletos actualizados correctamente.')
            return redirect('apuestas:panel_admin_inicio')
        else:
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
    else:
        form = ResultadoEventoForm()

    opciones = OpcionApuesta.objects.filter(id_mercado_evento__id_evento=evento).select_related('id_mercado_evento__id_tipo_mercado')
    return render(request, 'apuestas/admin_liquidar_evento.html', {'evento': evento, 'form': form, 'opciones': opciones})
