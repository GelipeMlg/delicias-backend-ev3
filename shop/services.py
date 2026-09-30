from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import Day, Order, Sale, Audit

def owner(user): return user.is_authenticated and user.is_active and user.is_superuser
def require_owner(user):
    if not owner(user): raise PermissionDenied('Se requiere el rol de dueña.')
def used(day): return Order.objects.filter(day=day).exclude(status=Order.Status.CANCELLED).count()
def audit(user, action, obj, **details):
    Audit.objects.create(actor=user, action=action, resource=f'{obj._meta.model_name}:{obj.pk}', details=details)

def lock_day(date):
    Day.objects.get_or_create(date=date)
    return Day.objects.select_for_update().get(date=date)

@transaction.atomic
def reserve(user, data):
    date = data.pop('date')
    if date < timezone.localdate(): raise ValidationError('La fecha ya pasó.')
    day = lock_day(date)
    if day.blocked or used(day) >= day.capacity: raise ValidationError('Fecha bloqueada o sin cupos.')
    product = data['product']
    product.refresh_from_db()
    if not product.active: raise ValidationError('El producto fue retirado.')
    order = Order.objects.create(user=user, day=day, product_name=product.name, **data)
    audit(user, 'solicitar', order)
    return order

@transaction.atomic
def configure(user, date, data):
    require_owner(user)
    day = lock_day(date)
    if data['capacity'] < used(day): raise ValidationError('La capacidad es menor a los pedidos comprometidos.')
    day.capacity, day.blocked = data['capacity'], data['blocked']
    day.save()
    audit(user, 'configurar', day, capacity=day.capacity, blocked=day.blocked)
    return day

@transaction.atomic
def transition(user, order_id, action, amount=None, version=None):
    initial = Order.objects.get(pk=order_id)
    day = lock_day(initial.day_id)
    order = Order.objects.select_for_update().get(pk=order_id)
    if not owner(user) and order.user_id != user.pk: raise PermissionDenied()
    previous = order.status
    if action == 'quote':
        require_owner(user)
        if previous not in ['solicitado','cotizado','confirmado']: raise ValidationError('El pedido está cerrado.')
        if amount is None or not 1 <= amount <= 999999999: raise ValidationError('Monto inválido.')
        order.quote, order.status = amount, 'cotizado'
        order.quote_version += 1
    elif action == 'confirm':
        if previous != 'cotizado' or version != order.quote_version: raise ValidationError('Actualiza y acepta la cotización vigente.')
        if day.date < timezone.localdate() or day.blocked or used(day) > day.capacity: raise ValidationError('Fecha no disponible.')
        order.status = 'confirmado'
    elif action == 'cancel':
        if previous in ['entregado','cancelado']: raise ValidationError('El pedido ya está cerrado.')
        order.status = 'cancelado'
    elif action == 'deliver':
        require_owner(user)
        if previous != 'confirmado': raise ValidationError('Solo se entregan pedidos confirmados.')
        order.status = 'entregado'
        Sale.objects.create(order=order, concept=f'Pedido de {order.customer}', amount=order.quote, date=timezone.localdate())
    else: raise ValidationError('Operación desconocida.')
    order.save()
    audit(user, action, order, previous=previous, status=order.status, quote=order.quote, version=order.quote_version)
    return order
