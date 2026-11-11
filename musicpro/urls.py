from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalog.urls', namespace='catalog')),
    path('cuenta/', include('accounts.urls', namespace='accounts')),
    path('carrito/', include('cart.urls', namespace='cart')),
    path('pedidos/', include('orders.urls', namespace='orders')),
    path('bodega/', include('warehouse.urls', namespace='warehouse')),
    path('panel/', include('admin_panel.urls', namespace='admin_panel')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
