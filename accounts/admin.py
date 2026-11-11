from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CustomerProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type',
                    'rut', 'city', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_active', 'is_staff', 'is_superuser', 'city']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'rut']
    list_editable = ['is_active']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('user_type', 'phone', 'address', 'city', 'region',
                       'postal_code', 'rut', 'created_at', 'updated_at')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'phone', 'rut'),
        }),
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'loyalty_points', 'newsletter_subscribed']
    list_filter = ['newsletter_subscribed']
    search_fields = ['user__username', 'user__email', 'user__first_name']
    list_editable = ['loyalty_points', 'newsletter_subscribed']
