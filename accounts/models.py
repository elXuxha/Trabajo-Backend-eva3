from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Cliente'),
        ('admin', 'Administrador'),
        ('warehouse', 'Bodega'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    address = models.TextField(blank=True, verbose_name='Dirección')
    city = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    region = models.CharField(max_length=100, blank=True, verbose_name='Región')
    postal_code = models.CharField(max_length=10, blank=True, verbose_name='Código Postal')
    rut = models.CharField(max_length=12, blank=True, unique=True, null=True, verbose_name='RUT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    loyalty_points = models.IntegerField(default=0, verbose_name='Puntos de Fidelidad')
    newsletter_subscribed = models.BooleanField(default=False, verbose_name='Suscrito al Newsletter')

    class Meta:
        verbose_name = 'Perfil de Cliente'
        verbose_name_plural = 'Perfiles de Clientes'

    def __str__(self):
        return f"Perfil de {self.user.get_full_name()}"
