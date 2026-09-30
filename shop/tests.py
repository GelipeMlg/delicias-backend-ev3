from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.hashers import identify_hasher
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Product,Day,Order,Sale,Expense,Audit

class BackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser('duena',password='Ejemplo-Privado-9276')
        cls.customer = User.objects.create_user('cliente',password='Ejemplo-Cliente-9276')
        cls.other = User.objects.create_user('otro',password='Ejemplo-Otro-9276')
        cls.product = Product.objects.create(name='Torta',description='Chocolate',price=25000)
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()
        self.date = timezone.localdate()+timedelta(days=2)
    def login(self,user=None): self.client.force_authenticate(user or self.customer)
    def reserve(self):
        return self.client.post('/api/orders/',{'customer':'Persona de prueba','contact':'contacto ficticio',
            'product':str(self.product.pk),'quantity':1,'date':str(self.date),'time':'16:00'},format='json')
    def path(self,order,action): return f'/api/orders/{order}/{action}/'
    def quoted(self):
        self.login()
        result = self.reserve()
        self.assertEqual(result.status_code,201,result.data)
        order = result.data['id']
        self.login(self.owner)
        response = self.client.post(self.path(order,'quote'),{'amount':30000})
        self.assertEqual(response.status_code,200,response.data)
        return order
    def test_public_catalog_and_protected_write(self):
        self.assertEqual(self.client.get('/api/products/').status_code,200)
        self.assertEqual(self.client.post('/api/products/',{}).status_code,401)
        self.login()
        self.assertEqual(self.client.post('/api/products/',{}).status_code,403)
    def test_register_cannot_escalate_role(self):
        response = self.client.post('/api/register/',{'username':'nuevo','email':'nuevo@example.test',
            'password':'Pasteles-Distintos-9842','is_superuser':True,'is_staff':True},format='json')
        self.assertEqual(response.status_code,201,response.data)
        self.assertFalse(User.objects.get(username='nuevo').is_superuser)
        self.assertFalse(User.objects.get(username='nuevo').is_staff)
    def test_weak_password_rejected(self):
        self.assertEqual(self.client.post('/api/register/',{'username':'nuevo','email':'a@example.test','password':'1234'}).status_code,400)
    def test_bcrypt_and_login_session(self):
        self.assertEqual(identify_hasher(self.owner.password).algorithm,'bcrypt_sha256')
        self.assertTrue(self.client.login(username='duena',password='Ejemplo-Privado-9276'))
        self.assertTrue(self.client.get('/api/session/').data['owner'])
    def test_real_csrf_required_for_session_write(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username='duena',password='Ejemplo-Privado-9276')
        self.assertEqual(client.post('/api/products/',{'name':'Otra','description':'Prueba','price':10}).status_code,403)
        token = client.get('/api/session/').data['csrfToken']
        self.assertEqual(client.post('/api/products/',{'name':'Otra','description':'Prueba','price':10},HTTP_X_CSRFTOKEN=token).status_code,201)
    def test_capacity_and_cancel_release(self):
        Day.objects.create(date=self.date,capacity=1)
        self.login()
        order = self.reserve().data['id']
        self.assertEqual(self.reserve().status_code,400)
        self.assertEqual(self.client.get('/api/days/availability/',{'date':str(self.date)}).data['available'],0)
        self.assertEqual(self.client.post(self.path(order,'cancel')).status_code,200)
        self.assertEqual(self.reserve().status_code,201)
    def test_cannot_read_or_cancel_another_customers_order(self):
        self.login()
        order = self.reserve().data['id']
        self.login(self.other)
        self.assertEqual(self.client.get('/api/orders/').data['count'],0)
        self.assertEqual(self.client.get(f'/api/orders/{order}/').status_code,404)
        self.assertEqual(self.client.post(self.path(order,'cancel')).status_code,404)
    def test_customer_cannot_quote_or_access_finances(self):
        self.login()
        order = self.reserve().data['id']
        self.assertEqual(self.client.post(self.path(order,'quote'),{'amount':1}).status_code,403)
        for path in ['sales','expenses','audit','summary']:
            self.assertEqual(self.client.get(f'/api/{path}/').status_code,403)
    def test_requote_requires_current_version(self):
        order = self.quoted()
        self.login()
        self.assertEqual(self.client.post(self.path(order,'confirm'),{'version':1}).status_code,200)
        self.login(self.owner)
        self.client.post(self.path(order,'quote'),{'amount':32000})
        self.login()
        self.assertEqual(self.client.post(self.path(order,'confirm'),{'version':1}).status_code,400)
        self.assertEqual(self.client.post(self.path(order,'confirm'),{'version':2}).status_code,200)
    def test_deliver_once_and_finance_correction(self):
        order = self.quoted()
        self.client.post(self.path(order,'confirm'),{'version':1})
        self.assertEqual(self.client.post(self.path(order,'deliver')).status_code,200)
        self.assertEqual(self.client.post(self.path(order,'deliver')).status_code,400)
        self.assertEqual(Sale.objects.count(),1)
        sale = Sale.objects.get()
        self.assertEqual(self.client.patch(f'/api/sales/{sale.pk}/',{'amount':31000},format='json').status_code,200)
        expense = self.client.post('/api/expenses/',{'concept':'Harina','amount':5000,'date':str(self.date),'category':'insumos'},format='json')
        self.assertEqual(expense.status_code,201,expense.data)
        self.assertEqual(self.client.get('/api/summary/').data['balance'],26000)
        self.client.delete(f'/api/expenses/{expense.data["id"]}/')
        self.assertEqual(self.client.get('/api/summary/').data['balance'],31000)
        self.assertTrue(Expense.objects.get().voided)
        self.assertGreater(Audit.objects.count(),3)
    def test_capacity_cannot_drop_below_committed(self):
        self.login()
        self.reserve()
        self.login(self.owner)
        self.assertEqual(self.client.post('/api/days/configure/',{'date':str(self.date),'capacity':0,'blocked':False},format='json').status_code,400)
    def test_retired_product_keeps_history(self):
        self.login()
        self.reserve()
        self.login(self.owner)
        self.assertEqual(self.client.delete(f'/api/products/{self.product.pk}/').status_code,204)
        self.login()
        self.assertEqual(self.client.get('/api/products/').data['count'],0)
        self.assertEqual(self.reserve().status_code,400)
        self.assertEqual(Order.objects.get().product_name,'Torta')
    def test_invalid_request_and_closed_day(self):
        Day.objects.create(date=self.date,blocked=True)
        self.login()
        self.assertEqual(self.reserve().status_code,400)
        self.assertEqual(Order.objects.count(),0)
    def test_home_logo_and_browsable_api(self):
        self.assertContains(self.client.get('/'),'Delicias de Mamá')
        self.assertEqual(self.client.get('/api/products/',HTTP_ACCEPT='text/html').status_code,200)

    def test_catalog_search_and_quote_form(self):
        self.assertEqual(self.client.get('/api/products/', {'search':'inexistente'}).data['count'],0)
        self.login(self.owner)
        page = self.client.get('/api/products/',HTTP_ACCEPT='text/html')
        self.assertContains(page,'Precio (CLP)')
        self.assertContains(page,'delicias.css')
        order = self.quoted()
        page = self.client.post(self.path(order,'quote'),{'amount':31000},HTTP_ACCEPT='text/html')
        self.assertContains(page,'name="amount"')
        self.assertContains(page,'Cotizar pedido')
