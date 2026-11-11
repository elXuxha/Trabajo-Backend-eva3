from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.warehouse_dashboard, name='dashboard'),
    path('stock/', views.warehouse_stock_list, name='stock_list'),
    path('stock/<int:product_id>/editar/', views.warehouse_stock_edit, name='stock_edit'),
    path('pedidos/', views.warehouse_orders, name='orders'),
    path('pedidos/<str:order_number>/', views.warehouse_order_detail, name='order_detail'),
]
