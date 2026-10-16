from django.core.management.base import BaseCommand
from django.db import transaction

from catalogos.models import Pais, Departamento, Municipio, Estado, Deporte, Liga, EquipoAtleta, TipoMercado, MetodoPago
from cuentas.models import Login, SuperAdministrador, PreguntaSeguridad

DEPARTAMENTOS_GT = [
    'Guatemala', 'Sacatepéquez', 'Chimaltenango', 'Escuintla', 'Quetzaltenango',
    'Huehuetenango', 'Alta Verapaz', 'Petén', 'Izabal', 'Zacapa',
]

PREGUNTAS_SEGURIDAD = [
    '¿Cuál es el nombre de tu primera mascota?',
    '¿Cuál es el nombre de tu escuela primaria?',
    '¿Cuál es el segundo nombre de tu madre?',
    '¿Cuál fue tu primer trabajo?',
    '¿Cuál es tu comida favorita?',
]

TIPOS_MERCADO = ['Ganador del partido', 'Total de goles/puntos (Over/Under)', 'Ambos equipos anotan', 'Marcador exacto']

METODOS_PAGO = [('Tarjeta de crédito/débito', 3.5), ('Transferencia bancaria', 0.0), ('Billetera electrónica', 1.5)]


class Command(BaseCommand):
    help = 'Carga catálogos base (país, departamentos, estados, tipos de mercado, etc.) y un super administrador inicial.'

    def handle(self, *args, **options):
        with transaction.atomic():
            estado_activo, _ = Estado.objects.get_or_create(nombre_estado='ACTIVO')
            Estado.objects.get_or_create(nombre_estado='INACTIVO')
            Estado.objects.get_or_create(nombre_estado='BLOQUEADO')
            Estado.objects.get_or_create(nombre_estado='ACTIVA')
            Estado.objects.get_or_create(nombre_estado='SUSPENDIDA')

            pais, _ = Pais.objects.get_or_create(nombre_pais='Guatemala', codigo_iso='GT')
            for nombre in DEPARTAMENTOS_GT:
                depto, creado = Departamento.objects.get_or_create(id_pais=pais, nombre_departamento=nombre)
                if creado:
                    Municipio.objects.get_or_create(id_departamento=depto, nombre_municipio=f'{nombre} (cabecera)')

            for texto in PREGUNTAS_SEGURIDAD:
                PreguntaSeguridad.objects.get_or_create(texto_pregunta=texto)

            for nombre in TIPOS_MERCADO:
                TipoMercado.objects.get_or_create(nombre_mercado=nombre)

            for nombre, comision in METODOS_PAGO:
                MetodoPago.objects.get_or_create(nombre_metodo=nombre, defaults={'comision_porcentaje': comision})

            deporte_futbol, _ = Deporte.objects.get_or_create(nombre_deporte='Fútbol', id_estado=estado_activo)
            Deporte.objects.get_or_create(nombre_deporte='Baloncesto', id_estado=estado_activo)
            Liga.objects.get_or_create(id_deporte=deporte_futbol, id_pais=pais, nombre_liga='Liga Nacional de Guatemala')

            if not Login.objects.filter(tipo_usuario='SUPER_ADMIN').exists():
                login_sa = Login(id_sistema_us='superadmin@apuestasdeportivas.local',
                                  nombre_usuario='superadmin', tipo_usuario='SUPER_ADMIN')
                login_sa.set_password('CambiarInmediatamente1!')
                login_sa.save()
                SuperAdministrador.objects.create(
                    id_login=login_sa, nombre_completo='Super Administrador Inicial',
                    correo_maestro='superadmin@apuestasdeportivas.local',
                )
                self.stdout.write(self.style.WARNING(
                    'Super administrador creado -> usuario: superadmin / contraseña: CambiarInmediatamente1! '
                    '(cámbiala de inmediato desde el panel administrativo).'
                ))

        self.stdout.write(self.style.SUCCESS('Datos iniciales cargados correctamente.'))
