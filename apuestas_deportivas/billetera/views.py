from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from cuentas.auth_utils import requiere_sesion, obtener_login_actual
from catalogos.models import MetodoPago
from .models import Billetera, Transaccion, HistorialSaldoBilletera, CuentaBancariaUsuario, SolicitudRetiro
from .forms import DepositoForm, SolicitudRetiroForm, CuentaBancariaForm


@requiere_sesion(['USUARIO'])
def deposito(request):
    login_obj = obtener_login_actual(request)
    billetera = login_obj.usuario.billetera

    if request.method == 'POST':
        form = DepositoForm(request.POST)
        if form.is_valid():
            monto = form.cleaned_data['monto']
            with transaction.atomic():
                billetera_bloqueada = Billetera.objects.select_for_update().get(pk=billetera.pk)
                saldo_anterior = billetera_bloqueada.saldo_disponible
                billetera_bloqueada.saldo_disponible += monto
                billetera_bloqueada.save(update_fields=['saldo_disponible'])

                Transaccion.objects.create(
                    id_billetera=billetera_bloqueada, id_metodo_pago_id=form.cleaned_data['id_metodo_pago'],
                    tipo_transaccion='DEPOSITO', monto=monto,
                )
                HistorialSaldoBilletera.objects.create(
                    id_billetera=billetera_bloqueada, saldo_anterior=saldo_anterior,
                    saldo_nuevo=billetera_bloqueada.saldo_disponible, monto_movimiento=monto,
                    tipo_operacion='DEPOSITO',
                )
            messages.success(request, f'Depósito de Q{monto} realizado correctamente.')
            return redirect('apuestas:panel_usuario_inicio')
        else:
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
    else:
        form = DepositoForm()

    return render(request, 'billetera/deposito.html', {
        'form': form, 'billetera': billetera, 'metodos_pago': MetodoPago.objects.all(),
    })


@requiere_sesion(['USUARIO'])
def mis_cuentas_bancarias(request):
    login_obj = obtener_login_actual(request)
    usuario = login_obj.usuario
    if request.method == 'POST':
        form = CuentaBancariaForm(request.POST)
        if form.is_valid():
            CuentaBancariaUsuario.objects.create(id_usuario=usuario, **form.cleaned_data)
            messages.success(request, 'Cuenta bancaria agregada.')
            return redirect('billetera:mis_cuentas_bancarias')
    else:
        form = CuentaBancariaForm()
    cuentas = usuario.cuentas_bancarias.all()
    return render(request, 'billetera/mis_cuentas_bancarias.html', {'form': form, 'cuentas': cuentas})


@requiere_sesion(['USUARIO'])
def solicitar_retiro(request):
    login_obj = obtener_login_actual(request)
    usuario = login_obj.usuario
    billetera = usuario.billetera
    cuentas = usuario.cuentas_bancarias.all()

    if request.method == 'POST':
        form = SolicitudRetiroForm(request.POST)
        if form.is_valid():
            monto = form.cleaned_data['monto_solicitado']
            cuenta = get_object_or_404(CuentaBancariaUsuario, pk=form.cleaned_data['id_cuenta_bancaria'], id_usuario=usuario)
            if monto > billetera.saldo_disponible:
                messages.error(request, 'Saldo disponible insuficiente para este retiro.')
            else:
                SolicitudRetiro.objects.create(
                    id_billetera=billetera, id_cuenta_bancaria=cuenta,
                    monto_solicitado=monto, estado_solicitud='PENDIENTE',
                )
                messages.success(request, 'Solicitud de retiro enviada. Será revisada por un cajero.')
                return redirect('billetera:solicitar_retiro')
        else:
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
    else:
        form = SolicitudRetiroForm()

    solicitudes = billetera.solicitudes_retiro.order_by('-fecha_solicitud')
    return render(request, 'billetera/solicitar_retiro.html', {
        'form': form, 'cuentas': cuentas, 'solicitudes': solicitudes, 'billetera': billetera,
    })


# --------------------------------------------------------------------------
# Gestión administrativa (rol cajero) de solicitudes de retiro
# --------------------------------------------------------------------------
@requiere_sesion(['ADMIN', 'SUPER_ADMIN'])
def admin_solicitudes_retiro(request):
    from apuestas.views import _rol_admin_actual
    rol, login_obj = _rol_admin_actual(request)
    if rol not in ('CAJERO', 'SUPER_ADMIN'):
        messages.error(request, 'No tienes permisos para gestionar retiros.')
        return redirect('apuestas:panel_admin_inicio')

    if request.method == 'POST':
        id_solicitud = request.POST.get('id_solicitud')
        accion = request.POST.get('accion')
        solicitud = get_object_or_404(SolicitudRetiro, pk=id_solicitud)

        if solicitud.estado_solicitud != 'PENDIENTE':
            messages.error(request, 'Esta solicitud ya fue procesada.')
        elif accion == 'aprobar':
            with transaction.atomic():
                billetera_bloqueada = Billetera.objects.select_for_update().get(pk=solicitud.id_billetera_id)
                if solicitud.monto_solicitado > billetera_bloqueada.saldo_disponible:
                    messages.error(request, 'El usuario ya no cuenta con saldo disponible suficiente.')
                else:
                    saldo_anterior = billetera_bloqueada.saldo_disponible
                    billetera_bloqueada.saldo_disponible -= solicitud.monto_solicitado
                    billetera_bloqueada.save(update_fields=['saldo_disponible'])

                    Transaccion.objects.create(
                        id_billetera=billetera_bloqueada, tipo_transaccion='RETIRO',
                        monto=solicitud.monto_solicitado,
                    )
                    HistorialSaldoBilletera.objects.create(
                        id_billetera=billetera_bloqueada, saldo_anterior=saldo_anterior,
                        saldo_nuevo=billetera_bloqueada.saldo_disponible,
                        monto_movimiento=solicitud.monto_solicitado, tipo_operacion='RETIRO',
                    )
                    solicitud.estado_solicitud = 'PAGADA'
                    solicitud.save(update_fields=['estado_solicitud'])
                    messages.success(request, 'Retiro aprobado y pagado correctamente.')
        elif accion == 'rechazar':
            solicitud.estado_solicitud = 'RECHAZADA'
            solicitud.save(update_fields=['estado_solicitud'])
            messages.info(request, 'Solicitud rechazada.')

    solicitudes = SolicitudRetiro.objects.select_related('id_billetera__id_usuario', 'id_cuenta_bancaria').order_by('-fecha_solicitud')
    return render(request, 'billetera/admin_solicitudes_retiro.html', {'solicitudes': solicitudes})
