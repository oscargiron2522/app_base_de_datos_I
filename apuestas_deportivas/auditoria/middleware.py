import re
import time
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from .models import BitacoraSeguridad

# Patrones simples para detectar intentos de inyección SQL en cualquier
# parámetro GET/POST. Esto es una capa adicional; el ORM de Django ya
# parametriza las consultas, pero esta capa detecta y bloquea intentos
# evidentes y deja evidencia en bitácora.
PATRONES_SQLI = [
    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
    r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
    r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
    r"exec(\s|\+)+(s|x)p\w+",
    r"union(\s|\+|%20)+select",
    r"select.+from",
    r"insert(\s|\+|%20)+into",
    r"drop(\s|\+|%20)+table",
    r"update.+set.+=",
    r"delete(\s|\+|%20)+from",
    r"<script[\s>]",
]
PATRONES_SQLI_COMPILADOS = [re.compile(p, re.IGNORECASE) for p in PATRONES_SQLI]


def obtener_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def contiene_patron_malicioso(valor: str) -> bool:
    if not isinstance(valor, str) or not valor:
        return False
    return any(p.search(valor) for p in PATRONES_SQLI_COMPILADOS)


class SeguridadPerimetralMiddleware:
    """Middleware que:
    1) Detecta y bloquea patrones típicos de inyección SQL / XSS en la
       entrada (GET, POST, cabeceras) antes de que lleguen a las vistas.
    2) Aplica un límite de solicitudes por IP y por minuto (rate limiting)
       como mitigación básica de ataques de denegación de servicio (DDOS)
       a nivel de aplicación.
    Todos los eventos bloqueados se registran en tbl_bitacora_seguridad.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = obtener_ip(request)

        # --- 1) Rate limiting anti-DDOS ---------------------------------
        clave_cache = f'rl:{ip}'
        peticiones = cache.get(clave_cache, 0)
        if peticiones >= settings.SEGURIDAD_MAX_PETICIONES_POR_MINUTO:
            self._registrar(request, ip, 'DDOS', 'Límite de solicitudes por minuto excedido')
            return JsonResponse(
                {'error': 'Demasiadas solicitudes. Intenta nuevamente en un momento.'},
                status=429,
            )
        cache.set(clave_cache, peticiones + 1, timeout=60)

        # --- 2) Detección de inyección SQL / XSS ------------------------
        valores_a_revisar = list(request.GET.values()) + list(request.POST.values())
        for valor in valores_a_revisar:
            if contiene_patron_malicioso(str(valor)):
                self._registrar(request, ip, 'SQLI', f'Patrón sospechoso detectado: {str(valor)[:200]}')
                return HttpResponseForbidden('Solicitud rechazada: contenido no permitido.')

        return self.get_response(request)

    def _registrar(self, request, ip, tipo, detalle):
        try:
            BitacoraSeguridad.objects.create(
                tipo_evento=tipo,
                ip_origen=ip,
                ruta_solicitada=request.path[:255],
                detalle=detalle,
                bloqueado=True,
            )
        except Exception:
            # Nunca debe caer la aplicación por un fallo al auditar.
            pass
