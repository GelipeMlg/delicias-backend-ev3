from django.contrib import admin
from django.urls import path,include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter, APIRootView
from shop import views
from shop.auth_views import RegisterView, LoginView, RefreshView, LogoutView

class DeliciasRoot(APIRootView):
    """Elige un módulo para consultar registros y utilizar sus formularios. Los pedidos requieren sesión y las finanzas están reservadas a la dueña."""
    def get_view_name(self): return 'API de Delicias de Mamá'

class DeliciasRouter(DefaultRouter):
    APIRootView = DeliciasRoot

router = DeliciasRouter()
for prefix, view, basename in [
    ('products',views.ProductViewSet,'product'),('days',views.DayViewSet,'day'),
    ('orders',views.OrderViewSet,'order'),('sales',views.SaleViewSet,'sale'),
    ('expenses',views.ExpenseViewSet,'expense'),('audit',views.AuditViewSet,'audit')]:
    router.register(prefix,view,basename=basename)
api_patterns = [path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='token-login'),
    path('auth/refresh/', RefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='token-logout'),
    path('session/', views.session), path('summary/', views.summary), path('', include(router.urls))]
urlpatterns = [path('',TemplateView.as_view(template_name='portal.html')),path('admin/',admin.site.urls),
    path('api/v1/', include((api_patterns, 'api'), namespace='v1')),
    # Alias para los clientes previos, con los mismos permisos y límites de registro.
    path('api/register/',RegisterView.as_view()),path('api/session/',views.session),path('api/summary/',views.summary),
    path('api/',include(router.urls)),path('api-auth/',include('rest_framework.urls'))]
