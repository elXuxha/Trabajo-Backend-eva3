from django.db import models
from django.conf import settings
from catalog.models import Product
import uuid


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('processing', 'Preparando'),
        ('shipped', 'Enviado'),
        ('in_transit', 'En Tránsito'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', 'Tarjeta de Crédito'),
        ('debit_card', 'Tarjeta de Débito'),
        ('transfer', 'Transferencia Bancaria'),
        ('webpay', 'Webpay'),
        ('mercadopago', 'Mercado Pago'),
    )
    SHIPPING_CHOICES = (
        ('home', 'Despacho a Domicilio'),
        ('pickup', 'Retiro en Tienda'),
        ('express', 'Despacho Express (24h)'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, verbose_name='Número de Pedido')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending',
                               verbose_name='Estado')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES,
                                       verbose_name='Método de Pago')
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES,
                                        default='home', verbose_name='Método de Despacho')
    
    shipping_name = models.CharField(max_length=200, verbose_name='Nombre')
    shipping_address = models.TextField(verbose_name='Dirección de Despacho')
    shipping_city = models.CharField(max_length=100, verbose_name='Ciudad')
    shipping_region = models.CharField(max_length=100, verbose_name='Región')
    shipping_postal_code = models.CharField(max_length=10, verbose_name='Código Postal')
    shipping_phone = models.CharField(max_length=20, verbose_name='Teléfono')
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                         verbose_name='Costo de Despacho')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                    verbose_name='Descuento')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total')
    
    notes = models.TextField(blank=True, verbose_name='Notas')
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name='Número de Rastreo')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f'MP{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=300, verbose_name='Nombre del Producto')
    product_price = models.DecimalField(max_digits=10, decimal_places=2,
                                         verbose_name='Precio al Comprar')
    quantity = models.IntegerField(default=1, verbose_name='Cantidad')

    class Meta:
        verbose_name = 'Item del Pedido'
        verbose_name_plural = 'Items del Pedido'

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def subtotal(self):
        return self.product_price * self.quantity

    def save(self, *args, **kwargs):
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_price:
            self.product_price = self.product.price
        super().save(*args, **kwargs)
