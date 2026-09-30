import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

money = [MinValueValidator(1), MaxValueValidator(999999999)]

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    description = models.TextField(max_length=3000)
    price = models.PositiveIntegerField(validators=[MaxValueValidator(999999999)])
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Day(models.Model):
    date = models.DateField(primary_key=True)
    capacity = models.PositiveSmallIntegerField(default=3, validators=[MaxValueValidator(100)])
    blocked = models.BooleanField(default=False)
    def __str__(self): return str(self.date)

class Order(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'solicitado', 'Solicitado'
        QUOTED = 'cotizado', 'Cotizado'
        CONFIRMED = 'confirmado', 'Confirmado'
        DELIVERED = 'entregado', 'Entregado'
        CANCELLED = 'cancelado', 'Cancelado'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    customer = models.CharField(max_length=160)
    contact = models.CharField(max_length=160)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=160)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    day = models.ForeignKey(Day, on_delete=models.PROTECT)
    time = models.TimeField()
    flavor = models.CharField(max_length=300, blank=True)
    filling = models.CharField(max_length=300, blank=True)
    theme = models.CharField(max_length=500, blank=True)
    restrictions = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REQUESTED)
    quote = models.PositiveIntegerField(null=True, blank=True, validators=money)
    quote_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['day', 'status'])]
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gte=1, quantity__lte=100), name='valid_quantity')]

class Sale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, null=True, blank=True, on_delete=models.PROTECT)
    concept = models.CharField(max_length=300)
    amount = models.PositiveIntegerField(validators=money)
    date = models.DateField()
    voided = models.BooleanField(default=False)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(amount__gte=1, amount__lte=999999999), name='valid_sale_amount')]

class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    concept = models.CharField(max_length=300)
    amount = models.PositiveIntegerField(validators=money)
    date = models.DateField()
    category = models.CharField(max_length=20, choices=[(x,x) for x in ['insumos','costo_fijo','costo_variable','otro']])
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT)
    voided = models.BooleanField(default=False)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(amount__gte=1, amount__lte=999999999), name='valid_expense_amount')]

class Audit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=40)
    resource = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
