from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'product_price', 'quantity', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_method',
                    'shipping_method', 'total', 'created_at']
    list_filter = ['status', 'payment_method', 'shipping_method', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__first_name',
                     'user__last_name', 'shipping_name']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'subtotal', 'shipping_cost', 'discount', 'total']
    list_editable = ['status']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'product_name', 'product_price',
                    'quantity', 'subtotal']
    search_fields = ['order__order_number', 'product__name', 'product_name']
