from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Product, Day, Order, Sale, Expense, Audit


admin.site.site_header = 'Delicias de Mamá'
admin.site.site_title = 'Administración'


class ReadOnlyAdmin(admin.ModelAdmin):
    # Los cambios de negocio pasan por la API y sus reglas transaccionales.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(ReadOnlyAdmin):
    list_display = ['name', 'price', 'active']
    search_fields = ['name']


@admin.register(Order)
class OrderAdmin(ReadOnlyAdmin):
    list_display = [
        'id',
        'customer',
        'day',
        'status',
        'quote',
        'acciones',
    ]

    list_filter = ['status']
    search_fields = ['customer', 'contact']

    @admin.display(description='Acciones')
    def acciones(self, obj):
        quote_url = f'/api/v1/orders/{obj.pk}/quote/'
        deliver_url = f'/api/v1/orders/{obj.pk}/deliver/'

        botones = []

        if obj.status in ['solicitado', 'cotizado']:
            botones.append(
                format_html(
                    '<a style="padding:6px 10px;background:#a84b5c;color:white;'
                    'border-radius:5px;text-decoration:none;" href="{}">Cotizar</a>',
                    quote_url,
                )
            )

        if obj.status == 'confirmado':
            botones.append(
                format_html(
                    '<a style="padding:6px 10px;background:#5b7f5b;color:white;'
                    'border-radius:5px;text-decoration:none;" href="{}">Entregar</a>',
                    deliver_url,
                )
            )

        if not botones:
            return '-'

        return format_html(' &nbsp; '.join(str(boton) for boton in botones))


for model in [Day, Sale, Expense, Audit]:
    admin.site.register(model, ReadOnlyAdmin)