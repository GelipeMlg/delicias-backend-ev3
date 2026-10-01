from django.db import transaction
from django.db.models import Sum
from django.middleware.csrf import get_token
from rest_framework import viewsets, permissions, status, filters, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Product, Day, Order, Sale, Expense, Audit
from .serializers import (ProductSerializer, DaySerializer, OrderSerializer,
    ReserveSerializer, QuoteSerializer, ConfirmSerializer, SaleSerializer, ExpenseSerializer, AuditSerializer)
from . import services

class PresentationMixin:
    section = 'Delicias de Mamá'
    def get_view_name(self):
        actions = {'quote':'Cotizar pedido','confirm':'Aceptar cotización','cancel':'Cancelar pedido',
            'deliver':'Registrar entrega','configure':'Configurar agenda','availability':'Consultar cupos'}
        return actions.get(getattr(self,'action',None), self.section)

class OwnerOnly(permissions.BasePermission):
    def has_permission(self,request,view): return services.owner(request.user)

class CatalogPermission(permissions.BasePermission):
    def has_permission(self,request,view):
        return request.method in permissions.SAFE_METHODS or services.owner(request.user)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def session(request):
    return Response({'authenticated':request.user.is_authenticated,
        'username':request.user.get_username() if request.user.is_authenticated else None,
        'owner':services.owner(request.user),'csrfToken':get_token(request)})

class ProductViewSet(PresentationMixin, viewsets.ModelViewSet):
    """Catálogo del negocio. La dueña puede crear y editar productos. DELETE retira un producto conservando su historial. Usa Filtros para buscar por nombre o descripción."""
    section = 'Productos'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name','description']
    ordering_fields = ['name','price']
    serializer_class = ProductSerializer
    permission_classes = [CatalogPermission]
    def get_queryset(self):
        qs = Product.objects.order_by('name','id')
        return qs if services.owner(self.request.user) else qs.filter(active=True)
    @transaction.atomic
    def perform_create(self, serializer):
        obj = serializer.save()
        services.audit(self.request.user,'crear',obj,price=obj.price)
    @transaction.atomic
    def perform_update(self, serializer):
        obj = serializer.save()
        services.audit(self.request.user,'editar',obj,price=obj.price,active=obj.active)
    @transaction.atomic
    def perform_destroy(self, instance):
        instance.active = False
        instance.save(update_fields=['active'])
        services.audit(self.request.user,'retirar',instance)

class DayViewSet(PresentationMixin, viewsets.ReadOnlyModelViewSet):
    """Fechas configuradas, pedidos ocupados y cupos disponibles. La dueña puede configurar la capacidad desde la acción configure. Consulta una fecha con availability/?date=AAAA-MM-DD."""
    section = 'Agenda y disponibilidad'
    queryset = Day.objects.order_by('date')
    serializer_class = DaySerializer
    permission_classes = [CatalogPermission]
    lookup_value_regex = r'\d{4}-\d{2}-\d{2}'
    @action(detail=False, methods=['post'], permission_classes=[OwnerOnly])
    def configure(self, request):
        serializer = DaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        day = services.configure(request.user,data.pop('date'),data)
        return Response(DaySerializer(day).data)
    @action(detail=False, methods=['get'])
    def availability(self,request):
        from rest_framework import serializers
        date = serializers.DateField().run_validation(request.query_params.get('date'))
        day = Day.objects.filter(date=date).first()
        from django.utils import timezone
        if date < timezone.localdate(): return Response({'date':date,'available':0})
        return Response(DaySerializer(day).data if day else {'date':date,'capacity':3,'blocked':False,'used':0,'available':3})

class OrderViewSet(PresentationMixin, viewsets.ReadOnlyModelViewSet):
    """Consulta tus pedidos o envía una solicitud con el formulario.
    Abre el detalle de un pedido para cotizar, confirmar, cancelar
    o registrar su entrega según tus permisos.
    """

    section = 'Pedidos'
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        return {
            'create': ReserveSerializer,
            'quote': QuoteSerializer,
            'confirm': ConfirmSerializer,
            'cancel': serializers.Serializer,
            'deliver': serializers.Serializer,
        }.get(self.action, OrderSerializer)

    def get_queryset(self):
        qs = Order.objects.select_related('day', 'product')
        return qs if services.owner(self.request.user) else qs.filter(
            user=self.request.user
        )

    def create(self, request):
        serializer = ReserveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = services.reserve(
            request.user,
            serializer.validated_data
        )

        return Response(
            dict(
                OrderSerializer(
                    order,
                    context={'request': request}
                ).data
            ),
            status=201
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[OwnerOnly]
    )
    def quote(self, request, pk=None):
        """Escribe el monto total. Corregir una cotización exige
        que el cliente acepte la nueva versión.
        """

        order = self.get_object()

        data = QuoteSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        updated_order = services.transition(
            request.user,
            order.pk,
            'quote',
            **data.validated_data
        )

        return Response(
            dict(
                OrderSerializer(
                    updated_order,
                    context={'request': request}
                ).data
            )
        )

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Indica la quote_version que aparece en el pedido
        para aceptar exactamente esa cotización.
        """

        order = self.get_object()

        data = ConfirmSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        updated_order = services.transition(
            request.user,
            order.pk,
            'confirm',
            **data.validated_data
        )

        return Response(
            dict(
                OrderSerializer(
                    updated_order,
                    context={'request': request}
                ).data
            )
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        updated_order = services.transition(
            request.user,
            self.get_object().pk,
            'cancel'
        )

        return Response(
            dict(
                OrderSerializer(
                    updated_order,
                    context={'request': request}
                ).data
            )
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[OwnerOnly]
    )
    def deliver(self, request, pk=None):
        updated_order = services.transition(
            request.user,
            self.get_object().pk,
            'deliver'
        )

        return Response(
            dict(
                OrderSerializer(
                    updated_order,
                    context={'request': request}
                ).data
            )
        )

class FinanceViewSet(PresentationMixin, viewsets.ModelViewSet):
    """Registra o corrige un movimiento. DELETE lo anula sin borrar su historial; los anulados no se incluyen en el resumen financiero."""
    permission_classes = [OwnerOnly]
    @transaction.atomic
    def perform_create(self,serializer):
        obj = serializer.save()
        services.audit(self.request.user,'crear',obj,amount=obj.amount)
    @transaction.atomic
    def perform_update(self,serializer):
        obj = serializer.save()
        services.audit(self.request.user,'corregir',obj,amount=obj.amount)
    @transaction.atomic
    def perform_destroy(self,instance):
        instance.voided = True
        instance.save(update_fields=['voided'])
        services.audit(self.request.user,'anular',instance)

class SaleViewSet(FinanceViewSet):
    section = 'Ventas'
    queryset = Sale.objects.order_by('-date','id')
    serializer_class = SaleSerializer
class ExpenseViewSet(FinanceViewSet):
    section = 'Gastos'
    queryset = Expense.objects.order_by('-date','id')
    serializer_class = ExpenseSerializer
class AuditViewSet(PresentationMixin, viewsets.ReadOnlyModelViewSet):
    """Consulta quién realizó cada operación y cuándo. Este historial es de solo lectura."""
    section = 'Historial de operaciones'
    queryset = Audit.objects.order_by('-created_at')
    serializer_class = AuditSerializer
    permission_classes = [OwnerOnly]

@api_view(['GET'])
@permission_classes([OwnerOnly])
def summary(request):
    sales = Sale.objects.filter(voided=False).aggregate(total=Sum('amount'))['total'] or 0
    expenses = Expense.objects.filter(voided=False).aggregate(total=Sum('amount'))['total'] or 0
    return Response({'sales':sales,'expenses':expenses,'balance':sales-expenses,'currency':'CLP'})
