from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'access_tier', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('role', 'access_tier', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('POS permissions', {
            'fields': (
                'role',
                'access_tier',
                'two_factor_enabled',
                'two_factor_code',
                'two_factor_verified_at',
            )
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('POS permissions', {
            'fields': ('role', 'access_tier', 'two_factor_enabled')
        }),
    )
