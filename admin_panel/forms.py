from django import forms
from django.utils.text import slugify

from accounts.models import User, CustomerProfile
from catalog.models import Product


class AdminUserForm(forms.ModelForm):
    """Formulario propio para Crear y Editar usuarios (CRUD sin Django Admin)."""

    password = forms.CharField(
        label='Contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Déjala vacía para mantener la actual',
        }),
        help_text='Obligatoria solo al crear un usuario nuevo.',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'rut', 'user_type',
                  'phone', 'city', 'region', 'address', 'postal_code',
                  'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'nombreusuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'correo@ejemplo.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Apellido'}),
            'rut': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '12.345.678-9'}),
            'user_type': forms.Select(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+56 9 1234 5678'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Santiago'}),
            'region': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Metropolitana'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Dirección'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '7500000'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-mp-red focus:ring-mp-red'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-mp-red focus:ring-mp-red'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if not self.instance.pk and not password:
            raise forms.ValidationError('Debes indicar una contraseña para crear el usuario.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            if user.user_type == 'customer':
                CustomerProfile.objects.get_or_create(user=user)
            self._save_m2m()
        return user


class AdminProductForm(forms.ModelForm):
    """Formulario propio para Crear y Editar productos del catálogo (CRUD sin Django Admin)."""

    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'brand', 'price', 'original_price',
                  'stock', 'min_stock', 'short_description', 'description',
                  'is_active', 'is_featured', 'is_new', 'is_on_sale']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Fender Stratocaster Player'}),
            'sku': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'FEN-STR-001'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'brand': forms.Select(attrs={'class': 'form-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'original_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'short_description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Descripción corta'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-mp-red focus:ring-mp-red'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-mp-red focus:ring-mp-red'}),
            'is_new': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-mp-red focus:ring-mp-red'}),
            'is_on_sale': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-mp-red focus:ring-mp-red'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0.')
        return price

    def save(self, commit=True):
        product = super().save(commit=False)
        if not product.slug:
            base = slugify(product.name) or 'producto'
            slug, intento = base, 2
            while Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
                slug = f'{base}-{intento}'
                intento += 1
            product.slug = slug
        if commit:
            product.save()
            self._save_m2m()
        return product
