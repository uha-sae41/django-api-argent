from rest_framework import authentication
from rest_framework import exceptions
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ExternalTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Extraire le token de l'en-tête
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None

        # Format attendu: "Token xxx" ou "Bearer xxx"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() not in ('token', 'bearer'):
            return None

        token = parts[1]
        logger.debug(f"Tentative d'authentification avec token: {token[:5]}...")

        try:
            headers = {
                'Authorization': f'Token {token}'
            }

            response = requests.post(
                'http://127.0.0.1:8000/api/validate-token/',
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                user_data = response.json()
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