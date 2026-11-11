from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q
from catalog.models import Product, Category
from orders.models import Order


def warehouse_required(view_func):
    """Restringe la vista a bodega/admin. Siempre se usa bajo @login_required."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.user_type != 'warehouse' and not request.user.is_staff:
            messages.error(request, 'No tienes acceso a este panel.')
            return redirect('catalog:home')
        return view_func(request, *args, **kwargs)
    return _wrapped


@login_required
@warehouse_required
def warehouse_dashboard(request):
    low_stock_products = Product.objects.filter(
        is_active=True, stock__lte=F('min_stock')
    ).select_related('category', 'brand')
    
    pending_orders = Order.objects.filter(
        status__in=['pending', 'confirmed']
    ).select_related('user').order_by('created_at')
    
    processing_orders = Order.objects.filter(
        status='processing'
    ).select_related('user').order_by('created_at')
    
    total_products = Product.objects.filter(is_active=True).count()
    out_of_stock = Product.objects.filter(is_active=True, stock=0).count()
    
    context = {
        'low_stock_products': low_stock_products,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'low_stock_count': low_stock_products.count(),
        'pending_count': pending_orders.count(),
        'processing_count': processing_orders.count(),
    }
    return render(request, 'warehouse/dashboard.html', context)


@login_required
@warehouse_required
def warehouse_stock_list(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')
    
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )
    
    filter_type = request.GET.get('filter', '')
    if filter_type == 'low':
        products = products.filter(stock__lte=F('min_stock'), stock__gt=0)
    elif filter_type == 'out':
        products = products.filter(stock=0)
    elif filter_type == 'ok':
        products = products.filter(stock__gt=F('min_stock'))
    
    sort = request.GET.get('sort', 'name')
    if sort == 'stock_asc':
        products = products.order_by('stock')
    elif sort == 'stock_desc':
        products = products.order_by('-stock')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'sku':
        products = products.order_by('sku')
    
    context = {
        'products': products,
        'query': query,
        'current_filter': filter_type,
        'current_sort': sort,
    }
    return render(request, 'warehouse/stock_list.html', context)


@login_required
@warehouse_required
def warehouse_stock_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            new_stock = int(request.POST.get('stock', product.stock))
            new_min = int(request.POST.get('min_stock', product.min_stock))
        except (ValueError, TypeError):
            messages.error(request, 'Valores inválidos.')
            return redirect('warehouse:stock_list')
        
        if new_stock < 0:
            new_stock = 0
        if new_min < 0:
            new_min = 0
        
        product.stock = new_stock
        product.min_stock = new_min
        product.save(update_fields=['stock', 'min_stock', 'updated_at'])
        
        messages.success(request, f'Stock de {product.name} actualizado a {new_stock} unidades.')
        return redirect('warehouse:stock_list')
    
    context = {'product': product}
    return render(request, 'warehouse/stock_edit.html', context)


@login_required
@warehouse_required
def warehouse_orders(request):
    status_filter = request.GET.get('status', '')
    
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    else:
        orders = orders.filter(status__in=['pending', 'confirmed', 'processing', 'shipped'])
    
    context = {
        'orders': orders,
        'current_status': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'warehouse/orders.html', context)


@login_required
@warehouse_required
def warehouse_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        new_status = request.POST.get('status', order.status)
        tracking = request.POST.get('tracking_number', '').strip()
        
        valid_statuses = [c[0] for c in Order.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status
            if tracking:
                order.tracking_number = tracking
            order.save(update_fields=['status', 'tracking_number', 'updated_at'])
            messages.success(request, f'Pedido #{order.order_number} actualizado a {order.get_status_display()}.')
        
        return redirect('warehouse:order_detail', order_number=order.order_number)
    
    context = {'order': order}
    return render(request, 'warehouse/order_detail.html', context)
