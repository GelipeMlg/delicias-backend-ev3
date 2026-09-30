from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Product, Day, Order, Sale, Expense, Audit
from . import services

class SpanishLabels:
    """Etiquetas de formulario; conserva las claves JSON de la API."""
    def get_fields(self):
        fields = super().get_fields()
        labels = {'name':'Nombre','description':'Descripción','price':'Precio (CLP)',
            'active':'Disponible en el catálogo','date':'Fecha','capacity':'Capacidad de pedidos',
            'blocked':'Fecha bloqueada','customer':'Nombre del cliente','contact':'Contacto',
            'product':'Producto','quantity':'Cantidad','time':'Hora de entrega','flavor':'Sabor',
            'filling':'Relleno','theme':'Temática','restrictions':'Restricciones alimentarias',
            'concept':'Concepto','amount':'Monto (CLP)','category':'Categoría','order':'Pedido asociado',
            'version':'Versión de la cotización','username':'Nombre de usuario','email':'Correo electrónico',
            'password':'Contraseña'}
        for name, field in fields.items():
            if name in labels: field.label = labels[name]
            if name in ['price','amount']: field.help_text = 'Pesos chilenos enteros, sin puntos ni decimales.'
            if name == 'date': field.style = {**field.style, 'input_type':'date'}
            if name == 'time': field.style = {**field.style, 'input_type':'time'}
        return fields

class RegisterSerializer(SpanishLabels, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=256)
    class Meta:
        model = User
        fields = ['username','email','password']
        extra_kwargs = {'email': {'required': True}}
    def validate(self, data):
        try: validate_password(data['password'], User(username=data['username'],email=data['email']))
        except DjangoValidationError as error: raise serializers.ValidationError({'password': error.messages})
        return data
    def create(self, data): return User.objects.create_user(**data)

class ProductSerializer(SpanishLabels, serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id','name','description','price','active']

class DaySerializer(SpanishLabels, serializers.ModelSerializer):
    capacity = serializers.IntegerField(min_value=0, max_value=100, default=3)
    blocked = serializers.BooleanField(default=False)
    used = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    class Meta:
        model = Day
        fields = ['date','capacity','blocked','used','available']
        extra_kwargs = {'date': {'validators': []}}
    def get_used(self,obj): return services.used(obj)
    def get_available(self,obj): return 0 if obj.blocked else max(0,obj.capacity-services.used(obj))

class OrderSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='day_id', read_only=True)
    class Meta:
        model = Order
        fields = ['id','user','customer','contact','product','product_name','quantity','date','time',
                  'flavor','filling','theme','restrictions','status','quote','quote_version','created_at']
        read_only_fields = fields

class ReserveSerializer(SpanishLabels, serializers.ModelSerializer):
    date = serializers.DateField()
    class Meta:
        model = Order
        fields = ['customer','contact','product','quantity','date','time','flavor','filling','theme','restrictions']

    def validate_date(self, value):
        from django.utils import timezone
        if value < timezone.localdate():
            raise serializers.ValidationError('Elige una fecha actual o futura.')
        return value

    def validate_product(self, value):
        if not value.active:
            raise serializers.ValidationError('El producto fue retirado del catálogo.')
        return value

class QuoteSerializer(SpanishLabels, serializers.Serializer):
    amount = serializers.IntegerField(min_value=1,max_value=999999999)
class ConfirmSerializer(SpanishLabels, serializers.Serializer):
    version = serializers.IntegerField(min_value=1)

class SaleSerializer(SpanishLabels, serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = ['id','order','concept','amount','date','voided']
        read_only_fields = ['order','voided']

class ExpenseSerializer(SpanishLabels, serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id','order','concept','amount','date','category','voided']
        read_only_fields = ['voided']

class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audit
        fields = ['id','actor','action','resource','details','created_at']
