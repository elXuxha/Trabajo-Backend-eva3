import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'musicpro.settings'
django.setup()

from catalog.models import Branch, Category, Brand, Product
from accounts.models import User, CustomerProfile
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem

print('=== DATOS EN BASE DE DATOS ===')
print(f'Sucursales:     {Branch.objects.count()}')
print(f'Categorias:     {Category.objects.count()}')
print(f'Marcas:         {Brand.objects.count()}')
print(f'Productos:      {Product.objects.count()}')
print(f'Usuarios:       {User.objects.count()}')
print(f'Clientes:       {User.objects.filter(user_type="customer").count()}')
print(f'Perfiles:       {CustomerProfile.objects.count()}')
print(f'Pedidos:        {Order.objects.count()}')
print(f'Items pedido:   {OrderItem.objects.count()}')
print(f'Carritos:       {Cart.objects.count()}')
print(f'Items carrito:  {CartItem.objects.count()}')

print()
print('=== MIGRACIONES ===')
from django.db.migrations.recorder import MigrationRecorder
for m in MigrationRecorder.Migration.objects.filter(
    app__in=['accounts', 'catalog', 'cart', 'orders']
):
    print(f'  {m.app}.{m.name}')

print()
print('=== DJANGO ADMIN - Modelos registrados ===')
from django.contrib import admin
for model, model_admin in sorted(admin.site._registry.items(), key=lambda x: x[0].__name__):
    has_display = hasattr(model_admin, 'list_display') and len(model_admin.list_display) > 0
    has_filter = hasattr(model_admin, 'list_filter') and len(model_admin.list_filter) > 0
    has_search = hasattr(model_admin, 'search_fields') and len(model_admin.search_fields) > 0
    print(f'  {model.__name__:30s} display={has_display}  filter={has_filter}  search={has_search}')
