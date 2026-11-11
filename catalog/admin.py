from django.contrib import admin
from .models import Branch, Category, Brand, Product, ProductImage, ProductSpecification


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch_type', 'city', 'phone', 'is_active', 'created_at']
    list_filter = ['branch_type', 'is_active', 'city']
    search_fields = ['name', 'address', 'city', 'email']
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['sort_order', 'is_active']
    ordering = ['sort_order']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'brand', 'price', 'stock',
                    'is_active', 'is_featured', 'is_new', 'is_on_sale', 'created_at']
    list_filter = ['is_active', 'is_featured', 'is_new', 'is_on_sale', 'category', 'brand']
    search_fields = ['name', 'sku', 'description', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductSpecificationInline]
    list_editable = ['price', 'stock', 'is_active', 'is_featured', 'is_on_sale']
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'is_primary', 'sort_order']
    list_filter = ['is_primary']
    search_fields = ['product__name', 'alt_text']


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'value']
    search_fields = ['product__name', 'name', 'value']
