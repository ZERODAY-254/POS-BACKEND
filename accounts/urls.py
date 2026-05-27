from django.urls import path
from .views import (
    deactivate_user,
    login_view,
    logout_view,
    me_view,
    register_view,
    request_password_reset,
    reset_password,
    refresh_token_view,
    verify_two_factor,
)

urlpatterns = [

    path('login/', login_view, name='login'),
    path('me/', me_view, name='me'),
    path('refresh/', refresh_token_view, name='refresh_token_alias'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', refresh_token_view, name='refresh_token'),
    path('register/', register_view, name='register'),
    path('two-factor/verify/', verify_two_factor, name='verify_two_factor'),
    path('password-reset/request/', request_password_reset, name='request_password_reset'),
    path('password-reset/confirm/', reset_password, name='reset_password'),

    path(
        'deactivate/<int:user_id>/',
        deactivate_user,
        name='deactivate_user'
    ),

]
