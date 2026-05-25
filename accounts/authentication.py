from rest_framework import authentication, exceptions

from .jwt import decode_jwt
from .models import CustomUser


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode()
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        payload = decode_jwt(parts[1], expected_type='access')
        if not payload:
            raise exceptions.AuthenticationFailed('Invalid or expired token')

        try:
            user = CustomUser.objects.get(id=payload.get('sub'), is_active=True)
        except CustomUser.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed('User not found or inactive') from exc

        return user, payload
