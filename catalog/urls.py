from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('productos/', views.product_list_view, name='product_list'),
    path('producto/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('categoria/<slug:slug>/', views.category_detail_view, name='category_detail'),
]
