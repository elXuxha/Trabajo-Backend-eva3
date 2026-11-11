from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),

    # Usuarios: CRUD propio (sin Django Admin)
    path('usuarios/', views.admin_users, name='users'),
    path('usuarios/nuevo/', views.admin_user_create, name='user_create'),
    path('usuarios/<int:user_id>/editar/', views.admin_user_edit, name='user_edit'),
    path('usuarios/<int:user_id>/toggle/', views.admin_user_toggle, name='user_toggle'),

    # Productos: CRUD propio (sin Django Admin)
    path('productos/', views.admin_products, name='products'),
    path('productos/nuevo/', views.admin_product_create, name='product_create'),
    path('productos/<int:product_id>/editar/', views.admin_product_edit, name='product_edit'),
    path('productos/<int:product_id>/toggle/', views.admin_product_toggle, name='product_toggle'),

    # Pedidos
    path('pedidos/', views.admin_orders, name='orders'),
    path('pedidos/<str:order_number>/', views.admin_order_detail, name='order_detail'),
]
