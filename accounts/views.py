from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import CustomUser
from .serializers import UserSerializer
from .jwt import decode_jwt, token_pair_for_user

PASSWORD_RESET_CODES = {}


def generate_demo_code(user):
    return str(100000 + (user.id * 137) % 899999)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):

    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.two_factor_enabled:
            user.two_factor_code = generate_demo_code(user)
            user.two_factor_verified_at = None
            user.save(update_fields=['two_factor_code', 'two_factor_verified_at'])

        serializer = UserSerializer(user)

        return Response({
            'success': True,
            'user': serializer.data,
            'two_factor_required': user.two_factor_enabled,
            'verification_code': user.two_factor_code if user.two_factor_enabled else '',
            'tokens': {} if user.two_factor_enabled else token_pair_for_user(user),
        })

    return Response({
        'success': False,
        'message': 'Invalid credentials'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    role = request.data.get('role', 'customer')

    allowed_roles = ['customer', 'cashier', 'storekeeper', 'manager']

    if not username or not password:
        return Response({
            'success': False,
            'message': 'Username and password are required'
        })

    if role not in allowed_roles:
        return Response({
            'success': False,
            'message': 'You cannot create that type of account here'
        })

    if CustomUser.objects.filter(username=username).exists():
        return Response({
            'success': False,
            'message': 'Username already exists'
        })

    try:
        validate_password(password)
    except ValidationError as error:
        return Response({
            'success': False,
            'message': ' '.join(error.messages)
        })

    user = CustomUser(username=username, email=email, role=role)
    user.set_password(password)
    user.save()

    return Response({
        'success': True,
        'user': UserSerializer(user).data,
        'message': 'Account created successfully'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    username = request.data.get('username', '').strip()

    try:
        user = CustomUser.objects.get(username=username, is_active=True)
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Active user not found'
        })

    code = generate_demo_code(user)
    PASSWORD_RESET_CODES[username] = code

    return Response({
        'success': True,
        'code': code,
        'message': 'Password reset code generated'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    username = request.data.get('username', '').strip()
    code = request.data.get('code', '').strip()
    new_password = request.data.get('new_password', '')

    if PASSWORD_RESET_CODES.get(username) != code:
        return Response({
            'success': False,
            'message': 'Invalid reset code'
        })

    try:
        user = CustomUser.objects.get(username=username, is_active=True)
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Active user not found'
        })

    try:
        validate_password(new_password, user)
    except ValidationError as error:
        return Response({
            'success': False,
            'message': ' '.join(error.messages)
        })

    user.set_password(new_password)
    user.save()
    PASSWORD_RESET_CODES.pop(username, None)

    return Response({
        'success': True,
        'message': 'Password reset successfully'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_two_factor(request):
    username = request.data.get('username', '').strip()
    code = request.data.get('code', '').strip()

    try:
        user = CustomUser.objects.get(username=username, is_active=True)
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Active user not found'
        })

    if not user.two_factor_enabled:
        return Response({
            'success': True,
            'user': UserSerializer(user).data,
            'message': 'Two-factor authentication is not required'
        })

    if user.two_factor_code != code:
        return Response({
            'success': False,
            'message': 'Invalid verification code'
        })

    user.two_factor_verified_at = timezone.now()
    user.two_factor_code = ''
    user.save(update_fields=['two_factor_verified_at', 'two_factor_code'])

    return Response({
        'success': True,
        'user': UserSerializer(user).data,
        'tokens': token_pair_for_user(user),
        'message': 'Two-factor authentication verified'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_user(request, user_id):

    if request.user.role != 'admin':
        return Response({
            'success': False,
            'message': 'Permission denied'
        })

    user = get_object_or_404(CustomUser, id=user_id)

    user.is_active = False
    user.save()

    return Response({
        'success': True,
        'message': 'User deactivated successfully'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response({
        'success': True,
        'user': UserSerializer(request.user).data,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    refresh_token = request.data.get('refresh', '').strip()
    payload = decode_jwt(refresh_token, expected_type='refresh')

    if not payload:
        return Response({
            'success': False,
            'message': 'Invalid or expired refresh token'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(id=payload.get('sub'), is_active=True)
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found or inactive'
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'tokens': token_pair_for_user(user),
        'user': UserSerializer(user).data,
    })
