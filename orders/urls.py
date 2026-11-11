from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirmacion/<str:order_number>/', views.order_confirmation_view, name='order_confirmation'),
    path('<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('<str:order_number>/seguimiento/', views.order_tracking_view, name='order_tracking'),
]
