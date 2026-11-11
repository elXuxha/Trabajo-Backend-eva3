from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from catalog.models import Product, Category
from orders.models import Order

from .forms import AdminUserForm, AdminProductForm


def staff_required(view_func):
    """Restringe la vista a administradores. Siempre se usa bajo @login_required."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
            messages.error(request, 'No tienes acceso a este panel.')
            return redirect('catalog:home')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ---------------------------------------------------------------- Dashboard
@login_required
@staff_required
def admin_dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_orders = Order.objects.count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_week = Order.objects.filter(created_at__date__gte=week_ago).count()

    total_revenue = Order.objects.exclude(status='cancelled').aggregate(
        total=Sum('total'))['total'] or 0
    revenue_today = Order.objects.exclude(status='cancelled').filter(
        created_at__date=today
    ).aggregate(total=Sum('total'))['total'] or 0

    total_users = User.objects.filter(user_type='customer').count()
    new_users_week = User.objects.filter(
        user_type='customer', created_at__date__gte=week_ago
    ).count()

    total_products = Product.objects.filter(is_active=True).count()
    low_stock = Product.objects.filter(
        is_active=True, stock__lte=F('min_stock')
    ).count()

    recent_orders = Order.objects.all().select_related('user')[:10]
    pending_orders = Order.objects.filter(
        status__in=['pending', 'confirmed']
    ).count()

    status_stats = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    context = {
        'total_orders': total_orders,
        'orders_today': orders_today,
        'orders_week': orders_week,
        'total_revenue': total_revenue,
        'revenue_today': revenue_today,
        'total_users': total_users,
        'new_users_week': new_users_week,
        'total_products': total_products,
        'low_stock': low_stock,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'status_stats': status_stats,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ---------------------------------------------------------------- Usuarios (CRUD)
@login_required
@staff_required
def admin_users(request):
    users = User.objects.all().order_by('-created_at')
    query = request.GET.get('q', '')
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(rut__icontains=query)
        )
    user_type = request.GET.get('type', '')
    if user_type:
        users = users.filter(user_type=user_type)
    context = {
        'users': users,
        'query': query,
        'current_type': user_type,
    }
    return render(request, 'admin_panel/users.html', context)


@login_required
@staff_required
def admin_user_create(request):
    if request.method == 'POST':
        form = AdminUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario {user.username} creado correctamente.')
            return redirect('admin_panel:users')
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = AdminUserForm()
    context = {'form': form, 'accion': 'Crear', 'titulo': 'Nuevo Usuario'}
    return render(request, 'admin_panel/user_form.html', context)


@login_required
@staff_required
def admin_user_edit(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=usuario)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario {user.username} actualizado correctamente.')
            return redirect('admin_panel:users')
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = AdminUserForm(instance=usuario)
    context = {'form': form, 'accion': 'Editar', 'titulo': f'Editar: {usuario.username}',
               'objeto': usuario}
    return render(request, 'admin_panel/user_form.html', context)


@login_required
@staff_required
@require_POST
def admin_user_toggle(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.id == request.user.id:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
    else:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        status = 'activado' if user.is_active else 'desactivado'
        messages.success(request, f'Usuario {user.username} {status}.')
    return redirect('admin_panel:users')


# ---------------------------------------------------------------- Productos (CRUD)
@login_required
@staff_required
def admin_products(request):
    products = Product.objects.all().select_related('category', 'brand')
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )
    category = request.GET.get('category', '')
    if category:
        products = products.filter(category__slug=category)
    categories = Category.objects.filter(is_active=True)
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'current_category': category,
    }
    return render(request, 'admin_panel/products.html', context)


@login_required
@staff_required
def admin_product_create(request):
    if request.method == 'POST':
        form = AdminProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Producto {product.name} creado correctamente.')
            return redirect('admin_panel:products')
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = AdminProductForm()
    context = {'form': form, 'accion': 'Crear', 'titulo': 'Nuevo Producto'}
    return render(request, 'admin_panel/product_form.html', context)


@login_required
@staff_required
def admin_product_edit(request, product_id):
    producto = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = AdminProductForm(request.POST, instance=producto)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Producto {product.name} actualizado correctamente.')
            return redirect('admin_panel:products')
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = AdminProductForm(instance=producto)
    context = {'form': form, 'accion': 'Editar', 'titulo': f'Editar: {producto.name}',
               'objeto': producto}
    return render(request, 'admin_panel/product_form.html', context)


@login_required
@staff_required
@require_POST
def admin_product_toggle(request, product_id):
    """Desactiva / reactiva un producto del catálogo (baja lógica)."""
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    estado = 'activado' if product.is_active else 'desactivado'
    messages.success(request, f'Producto {product.name} {estado}.')
    return redirect('admin_panel:products')


# ---------------------------------------------------------------- Pedidos
@login_required
@staff_required
def admin_orders(request):
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    context = {
        'orders': orders,
        'current_status': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/orders.html', context)


@login_required
@staff_required
def admin_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        new_status = request.POST.get('status', order.status)
        valid_statuses = [c[0] for c in Order.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status
            tracking = request.POST.get('tracking_number', '').strip()
            if tracking:
                order.tracking_number = tracking
            order.save(update_fields=['status', 'tracking_number', 'updated_at'])
            messages.success(request, f'Pedido #{order.order_number} actualizado.')
        return redirect('admin_panel:order_detail', order_number=order.order_number)
    context = {'order': order}
    return render(request, 'admin_panel/order_detail.html', context)
