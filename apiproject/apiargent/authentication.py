import requests
import logging
from django.conf import settings
from django.core.cache import cache
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)

class ExternalTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() not in ('token', 'bearer'):
            return None

        token = parts[1]
        cache_key = f"auth_token_{token}"
        user_data = cache.get(cache_key)

        if user_data:
            user = type('User', (), {
                **user_data,
                'is_authenticated': True,
                'is_active': True,
                '__str__': lambda self: str(self.user_id if hasattr(self, 'user_id') else 'Unknown')
            })
            return (user, token)

        try:
            headers = {'Authorization': f'Token {token}'}
            response = requests.post(
                settings.AUTH_API_URL,
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                user_data = response.json()
                cache.set(cache_key, user_data, timeout=300)  # 5 minutes
                user = type('User', (), {
                    **user_data,
                    'is_authenticated': True,
                    'is_active': True,
                    '__str__': lambda self: str(self.user_id if hasattr(self, 'user_id') else 'Unknown')
                })
                return (user, token)
            elif response.status_code == 401:
                raise exceptions.AuthenticationFailed('Token expiré ou invalide')
            else:
                raise exceptions.AuthenticationFailed(f'Erreur d\'authentification: {response.status_code}')
        except requests.RequestException as e:
            raise exceptions.AuthenticationFailed(f'Erreur de connexion à l\'API: {str(e)}')