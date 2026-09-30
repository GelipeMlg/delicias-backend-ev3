"""Respuestas y límites comunes de la API. No almacenar tokens en logs."""
from rest_framework.views import exception_handler
from rest_framework.throttling import SimpleRateThrottle


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {'error': {'status': response.status_code,
                                   'code': getattr(exc, 'default_code', 'error'),
                                   'details': response.data}}
    return response


class LoginThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class RegisterThrottle(LoginThrottle):
    scope = 'register'


class RefreshThrottle(LoginThrottle):
    scope = 'refresh'
