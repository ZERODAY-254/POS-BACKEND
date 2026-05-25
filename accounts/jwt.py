import base64
import hashlib
import hmac
import json
import time

from django.conf import settings


def _base64url_encode(value):
    return base64.urlsafe_b64encode(value).decode().rstrip('=')


def _base64url_decode(value):
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(message):
    return _base64url_encode(
        hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    )


def create_jwt(user, token_type='access', lifetime_seconds=None):
    lifetime_seconds = lifetime_seconds or (3600 if token_type == 'access' else 604800)
    now = int(time.time())
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {
        'sub': user.id,
        'username': user.username,
        'role': user.role,
        'type': token_type,
        'iat': now,
        'exp': now + lifetime_seconds,
    }
    signing_input = '.'.join([
        _base64url_encode(json.dumps(header, separators=(',', ':')).encode()),
        _base64url_encode(json.dumps(payload, separators=(',', ':')).encode()),
    ])
    return f'{signing_input}.{_sign(signing_input)}'


def decode_jwt(token, expected_type='access'):
    try:
        header_part, payload_part, signature = token.split('.')
        signing_input = f'{header_part}.{payload_part}'
        if not hmac.compare_digest(signature, _sign(signing_input)):
            return None

        payload = json.loads(_base64url_decode(payload_part))
    except (ValueError, json.JSONDecodeError):
        return None

    if payload.get('exp', 0) < int(time.time()):
        return None

    if expected_type and payload.get('type') != expected_type:
        return None

    return payload


def token_pair_for_user(user):
    return {
        'access': create_jwt(user, 'access'),
        'refresh': create_jwt(user, 'refresh'),
    }
