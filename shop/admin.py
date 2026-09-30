from django.contrib import admin
from .models import Product,Day,Order,Sale,Expense,Audit

admin.site.site_header = 'Delicias de Mamá'
admin.site.site_title = 'Administración'

class ReadOnlyAdmin(admin.ModelAdmin):
    # Los cambios de negocio pasan por la API y sus reglas transaccionales.
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False

@admin.register(Product)
class ProductAdmin(ReadOnlyAdmin):
    list_display = ['name','price','active']
    search_fields = ['name']
@admin.register(Order)
class OrderAdmin(ReadOnlyAdmin):
    list_display = ['id','customer','day','status','quote']
    list_filter = ['status']
for model in [Day,Sale,Expense,Audit]: admin.site.register(model,ReadOnlyAdmin)
