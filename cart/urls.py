from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='cart_detail'),
    path('agregar/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('eliminar/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('actualizar/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('api/count/', views.cart_count_api, name='cart_count'),
]
