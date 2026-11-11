from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category, Brand


def home_view(request):
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    new_products = Product.objects.filter(is_new=True, is_active=True)[:8]
    sale_products = Product.objects.filter(is_on_sale=True, is_active=True)[:8]
    categories = Category.objects.filter(is_active=True, parent=None)[:6]
    context = {
        'featured_products': featured_products,
        'new_products': new_products,
        'sale_products': sale_products,
        'categories': categories,
    }
    return render(request, 'catalog/home.html', context)


def product_list_view(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__name__icontains=query)
        )
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    brand_slug = request.GET.get('brand')
    if brand_slug:
        brand = get_object_or_404(Brand, slug=brand_slug)
        products = products.filter(brand=brand)
    sort = request.GET.get('sort', '-created_at')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'popular':
        products = products.order_by('-views_count')
    else:
        products = products.order_by('-created_at')
    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'query': query,
        'current_sort': sort,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    product.views_count += 1
    product.save(update_fields=['views_count'])
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)[:4]
    specifications = product.specifications.all()
    images = product.images.all()
    context = {
        'product': product,
        'related_products': related_products,
        'specifications': specifications,
        'images': images,
    }
    return render(request, 'catalog/product_detail.html', context)


def category_detail_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    subcategories = category.children.filter(is_active=True)
    sort = request.GET.get('sort', '-created_at')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    context = {
        'category': category,
        'products': products,
        'subcategories': subcategories,
        'current_sort': sort,
    }
    return render(request, 'catalog/category_detail.html', context)
