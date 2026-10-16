from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError


class DepositoForm(forms.Form):
    id_metodo_pago = forms.IntegerField(label='Método de pago')
    monto = forms.DecimalField(max_digits=14, decimal_places=2, label='Monto a depositar')

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if monto <= Decimal('0'):
            raise ValidationError('El monto debe ser mayor a cero.')
        if monto > Decimal('50000'):
            raise ValidationError('El monto excede el límite permitido por transacción.')
        return monto


class SolicitudRetiroForm(forms.Form):
    id_cuenta_bancaria = forms.IntegerField(label='Cuenta bancaria destino')
    monto_solicitado = forms.DecimalField(max_digits=14, decimal_places=2, label='Monto a retirar')

    def clean_monto_solicitado(self):
        monto = self.cleaned_data['monto_solicitado']
        if monto <= Decimal('0'):
            raise ValidationError('El monto debe ser mayor a cero.')
        return monto


class CuentaBancariaForm(forms.Form):
    nombre_banco = forms.CharField(max_length=100, label='Banco')
    numero_cuenta = forms.CharField(max_length=40, label='Número de cuenta')
    tipo_cuenta = forms.ChoiceField(choices=[('MONETARIA', 'Monetaria'), ('AHORRO', 'Ahorro')], label='Tipo de cuenta')
