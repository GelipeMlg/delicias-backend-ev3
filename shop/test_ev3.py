from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from .models import Product, Order
from .security import LoginThrottle, RegisterThrottle


class EvaluationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser('owner_ev3', password='Propietaria-Segura-8341')
        cls.customer = User.objects.create_user('client_ev3', password='Cliente-Seguro-8921')
        cls.product = Product.objects.create(name='Torta', description='Chocolate', price=25000)

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def tokens(self, owner=False):
        result = self.client.post('/api/v1/auth/login/', {
            'username': 'owner_ev3' if owner else 'client_ev3',
            'password': 'Propietaria-Segura-8341' if owner else 'Cliente-Seguro-8921'}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        return result.data

    def authenticate(self, owner=False):
        tokens = self.tokens(owner)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        return tokens

    def test_login_tokens_and_private_resource(self):
        tokens = self.authenticate()
        self.assertIn('refresh', tokens)
        self.assertEqual(self.client.get('/api/v1/orders/').status_code, 200)
        self.assertNotIn('password', tokens)

    def test_bad_credentials_standard_json(self):
        response = self.client.post('/api/v1/auth/login/', {'username':'client_ev3', 'password':'incorrecta'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error']['status'], 401)

    def test_anonymous_and_customer_permissions(self):
        self.assertEqual(self.client.get('/api/v1/expenses/').status_code, 401)
        self.authenticate()
        self.assertEqual(self.client.get('/api/v1/expenses/').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/products/', {}).status_code, 403)

    def test_registration_never_grants_owner_or_echoes_password(self):
        response = self.client.post('/api/v1/auth/register/', {'username':'safe_user',
            'email':'safe@example.test', 'password':'NoPublicar-Prueba-8291',
            'is_superuser':True, 'is_staff':True}, format='json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='safe_user')
        self.assertFalse(user.is_superuser or user.is_staff)
        self.assertNotIn('password', response.data)
        self.assertNotEqual(user.password, 'NoPublicar-Prueba-8291')

    def test_expired_and_forged_tokens_rejected(self):
        token = AccessToken.for_user(self.customer)
        token.set_exp(lifetime=timedelta(minutes=-1))
        for value in (str(token), 'not-a-valid-token'):
            self.client.credentials(HTTP_AUTHORIZATION='Bearer '+value)
            self.assertEqual(self.client.get('/api/v1/orders/').status_code, 401)

    def test_inactive_user_denied_with_issued_token(self):
        self.authenticate()
        self.customer.is_active = False
        self.customer.save(update_fields=['is_active'])
        self.assertEqual(self.client.get('/api/v1/orders/').status_code, 401)

    def test_refresh_rotates_and_old_refresh_is_rejected(self):
        tokens = self.tokens()
        first = self.client.post('/api/v1/auth/refresh/', {'refresh':tokens['refresh']})
        self.assertEqual(first.status_code, 200)
        self.assertNotEqual(first.data['refresh'], tokens['refresh'])
        self.assertEqual(self.client.post('/api/v1/auth/refresh/', {'refresh':tokens['refresh']}).status_code, 401)

    def test_logout_revokes_refresh(self):
        tokens = self.authenticate()
        self.assertEqual(self.client.post('/api/v1/auth/logout/', {'refresh':tokens['refresh']}).status_code, 204)
        self.client.credentials()
        self.assertEqual(self.client.post('/api/v1/auth/refresh/', {'refresh':tokens['refresh']}).status_code, 401)

    def test_logout_rejects_other_account_token_and_invalid_payload(self):
        owner_tokens = self.tokens(owner=True)
        self.authenticate()
        self.assertEqual(self.client.post('/api/v1/auth/logout/', {'refresh':owner_tokens['refresh']}).status_code, 400)
        self.assertEqual(self.client.post('/api/v1/auth/logout/', {'refresh':[]}, format='json').status_code, 400)

    def test_full_product_crud_http_methods(self):
        self.authenticate(owner=True)
        payload = {'name':'Empanadas', 'description':'Bandeja salada', 'price':12000, 'active':True}
        created = self.client.post('/api/v1/products/', payload, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        url = '/api/v1/products/'+created.data['id']+'/'
        self.assertEqual(self.client.get(url).status_code, 200)
        payload['price'] = 13000
        self.assertEqual(self.client.put(url, payload, format='json').status_code, 200)
        self.assertEqual(self.client.patch(url, {'price':14000}, format='json').status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.client.credentials()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_invalid_price_and_bad_json(self):
        self.authenticate(owner=True)
        for price in (-1, 'texto', 1000000000):
            response = self.client.post('/api/v1/products/', {'name':'X','description':'Y','price':price}, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertIn('price', response.data['error']['details'])
        response = self.client.post('/api/v1/products/', '{malformado', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_search_treats_sql_as_text(self):
        response = self.client.get('/api/v1/products/', {'search':"'; DROP TABLE shop_product; --"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        self.assertEqual(response.data['count'], 0)

    def test_pagination(self):
        Product.objects.bulk_create([Product(name=f'Producto {n}', description='Prueba',price=100) for n in range(35)])
        response = self.client.get('/api/v1/products/')
        self.assertEqual(len(response.data['results']), 30)
        self.assertIsNotNone(response.data['next'])

    @override_settings(CORS_ALLOWED_ORIGINS=['https://frontend.example.test'])
    def test_cors_allowlist(self):
        good = self.client.get('/api/v1/products/', HTTP_ORIGIN='https://frontend.example.test')
        bad = self.client.get('/api/v1/products/', HTTP_ORIGIN='https://ajeno.example.test')
        self.assertEqual(good.headers.get('Access-Control-Allow-Origin'), 'https://frontend.example.test')
        self.assertNotIn('Access-Control-Allow-Origin', bad.headers)

    def test_login_rate_limit_ignores_spoofed_forwarded_header(self):
        with patch.object(LoginThrottle, 'rate', '2/minute', create=True):
            for n in range(2):
                self.assertEqual(self.client.post('/api/v1/auth/login/', {'username':'x','password':'x'},
                    HTTP_X_FORWARDED_FOR=f'10.0.0.{n}').status_code, 401)
            result = self.client.post('/api/v1/auth/login/', {'username':'x','password':'x'}, HTTP_X_FORWARDED_FOR='10.0.0.99')
            self.assertEqual(result.status_code, 429)
            self.assertIn('Retry-After', result.headers)

    def test_register_rate_limit(self):
        with patch.object(RegisterThrottle, 'rate', '1/minute', create=True):
            self.assertEqual(self.client.post('/api/v1/auth/register/', {}).status_code, 400)
            self.assertEqual(self.client.post('/api/v1/auth/register/', {}).status_code, 429)

    def test_customer_cannot_choose_order_owner(self):
        self.authenticate()
        result = self.client.post('/api/v1/orders/', {'user':self.owner.pk, 'status':'entregado',
            'quote':1, 'customer':'Persona', 'contact':'Contacto de prueba', 'product':str(self.product.pk),
            'date':str(timezone.localdate()+timedelta(days=2)), 'time':'16:00', 'quantity':1}, format='json')
        self.assertEqual(result.status_code, 201, result.data)
        order = Order.objects.get(pk=result.data['id'])
        self.assertEqual(order.user_id, self.customer.pk)
        self.assertEqual(order.status, 'solicitado')
        self.assertIsNone(order.quote)

    def test_full_expense_crud(self):
        self.authenticate(owner=True)
        data = {'concept':'Harina', 'amount':5000, 'date':str(timezone.localdate()), 'category':'insumos'}
        response = self.client.post('/api/v1/expenses/', data, format='json')
        self.assertEqual(response.status_code, 201)
        url = f'/api/v1/expenses/{response.data["id"]}/'
        data['amount'] = 6000
        self.assertEqual(self.client.put(url, data, format='json').status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get('/api/v1/summary/').data['expenses'], 0)
