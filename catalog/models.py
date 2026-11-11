from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Branch(models.Model):
    BRANCH_TYPE_CHOICES = (
        ('rock', 'Sucursal del Rock'),
        ('dj', 'Sucursal DJ'),
        ('reggaeton', 'Sucursal Reggaetón y Cumbia'),
        ('general', 'Sucursal General'),
    )
    
    name = models.CharField(max_length=200, verbose_name='Nombre')
    branch_type = models.CharField(max_length=20, choices=BRANCH_TYPE_CHOICES, verbose_name='Tipo')
    address = models.TextField(verbose_name='Dirección')
    city = models.CharField(max_length=100, verbose_name='Ciudad')
    phone = models.CharField(max_length=20, verbose_name='Teléfono')
    email = models.EmailField(verbose_name='Correo')
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'

    def __str__(self):
        return f"{self.name} - {self.city}"


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nombre')
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Descripción')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Imagen')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name='Categoría Padre')
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    sort_order = models.IntegerField(default=0, verbose_name='Orden')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})


class Brand(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nombre')
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, verbose_name='Logo')
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_active = models.BooleanField(default=True, verbose_name='Activa')

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=300, verbose_name='Nombre')
    slug = models.SlugField(unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    description = models.TextField(verbose_name='Descripción')
    short_description = models.CharField(max_length=300, blank=True, verbose_name='Descripción Corta')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio')
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                          verbose_name='Precio Original')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products',
                                  verbose_name='Categoría')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='products', verbose_name='Marca')
    stock = models.IntegerField(default=0, verbose_name='Stock')
    min_stock = models.IntegerField(default=5, verbose_name='Stock Mínimo')
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                  verbose_name='Peso (kg)')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_featured = models.BooleanField(default=False, verbose_name='Destacado')
    is_new = models.BooleanField(default=False, verbose_name='Nuevo')
    is_on_sale = models.BooleanField(default=False, verbose_name='En Oferta')
    views_count = models.IntegerField(default=0, verbose_name='Vistas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', verbose_name='Imagen')
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='Texto Alternativo')
    is_primary = models.BooleanField(default=False, verbose_name='Imagen Principal')
    sort_order = models.IntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Imagen del Producto'
        verbose_name_plural = 'Imágenes del Producto'
        ordering = ['sort_order']

    def __str__(self):
        return f"Imagen de {self.product.name}"


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=200, verbose_name='Nombre')
    value = models.CharField(max_length=500, verbose_name='Valor')

    class Meta:
        verbose_name = 'Especificación'
        verbose_name_plural = 'Especificaciones'

    def __str__(self):
        return f"{self.name}: {self.value}"
