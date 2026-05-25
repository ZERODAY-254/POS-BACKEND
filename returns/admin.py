from django.contrib import admin
from .models import Return


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):

    list_display = (
        'customer_name',
        'item_name',
        'amount',
        'status',
        'returned_at',
    )
    search_fields = ('customer_name', 'item_name', 'reason')
    list_filter = ('status',)
