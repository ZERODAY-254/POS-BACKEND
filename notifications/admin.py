from django.contrib import admin

from .models import Notification, NotificationChannel, NotificationLog, NotificationRule, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'severity', 'is_read', 'created_at')
    list_filter = ('channel', 'severity', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'read_at')


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_type', 'is_active', 'created_at')
    list_filter = ('channel_type', 'is_active', 'created_at')
    search_fields = ('name',)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'subject', 'is_active', 'created_at')
    list_filter = ('channel', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'body')


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'template', 'is_active', 'created_at')
    list_filter = ('event', 'is_active', 'created_at')
    search_fields = ('name',)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'channel', 'status', 'created_at', 'sent_at')
    list_filter = ('status', 'channel', 'created_at')
    search_fields = ('recipient', 'response')
