from django.core.management.base import BaseCommand
from shop.models import Product

class Command(BaseCommand):
    help = 'Carga el catálogo de ejemplo de Android; no crea usuarios ni contraseñas.'
    def handle(self,*args,**kwargs):
        for name, description,price in [
            ('Torta de celebración','Bizcocho y relleno a elección. Decoración personalizada.',25000),
            ('Coctelería dulce','Surtido para compartir en reuniones y celebraciones.',18000),
            ('Cupcakes decorados','Una propuesta de sabores y colores para tu ocasión.',12000)]:
            Product.objects.get_or_create(name=name,defaults={'description':description,'price':price})
        self.stdout.write(self.style.SUCCESS('Catálogo de ejemplo disponible.'))
