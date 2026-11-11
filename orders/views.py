from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import Order, OrderItem
from cart.models import Cart


@login_required
def checkout_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('catalog:product_list')
    
    items = cart.items.select_related('product').all()
    
    if request.method == 'POST':
        shipping_name = request.POST.get('shipping_name', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        shipping_city = request.POST.get('shipping_city', '').strip()
        shipping_region = request.POST.get('shipping_region', '').strip()
        shipping_phone = request.POST.get('shipping_phone', '').strip()
        
        errors = []
        if not shipping_name:
            errors.append('El nombre es obligatorio.')
        if not shipping_address:
            errors.append('La dirección es obligatoria.')
        if not shipping_city:
            errors.append('La ciudad es obligatoria.')
        if not shipping_region:
            errors.append('La región es obligatoria.')
        if not shipping_phone:
            errors.append('El teléfono es obligatorio.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            context = {
                'cart': cart,
                'items': items,
                'subtotal': cart.total,
                'shipping': cart.shipping_cost,
                'grand_total': cart.total + cart.shipping_cost,
            }
            return render(request, 'orders/checkout.html', context)
        
        shipping_method = request.POST.get('shipping_method', 'home')
        
        if shipping_method == 'express':
            shipping_cost = 12990
        elif shipping_method == 'pickup':
            shipping_cost = 0
        elif cart.total >= 150000:
            shipping_cost = 0
        elif cart.total >= 80000:
            shipping_cost = 5990
        else:
            shipping_cost = 9990
        
        order = Order(
            user=request.user,
            payment_method=request.POST.get('payment_method', 'credit_card'),
            shipping_method=shipping_method,
            shipping_name=shipping_name,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_region=shipping_region,
            shipping_postal_code=request.POST.get('shipping_postal_code', '').strip(),
            shipping_phone=shipping_phone,
            subtotal=cart.total,
            shipping_cost=shipping_cost,
            total=cart.total + shipping_cost,
            notes=request.POST.get('notes', '').strip(),
        )
        order.save()
        
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
            )
            product = item.product
            product.stock -= item.quantity
            if product.stock < 0:
                product.stock = 0
            product.save(update_fields=['stock'])
        
        cart.items.all().delete()
        messages.success(request, f'¡Pedido #{order.order_number} realizado exitosamente!')
        return redirect('orders:order_confirmation', order_number=order.order_number)
    
    context = {
        'cart': cart,
        'items': items,
        'subtotal': cart.total,
        'shipping': cart.shipping_cost,
        'grand_total': cart.total + cart.shipping_cost,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_confirmation_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def order_tracking_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    status_steps = [
        ('pending', 'Pedido Recibido', 'Tu pedido ha sido registrado.'),
        ('confirmed', 'Confirmado', 'Tu pago ha sido verificado.'),
        ('processing', 'Preparando', 'Estamos preparando tu pedido.'),
        ('shipped', 'Enviado', 'Tu pedido ha sido despachado.'),
        ('in_transit', 'En Tránsito', 'Tu pedido está en camino.'),
        ('delivered', 'Entregado', 'Tu pedido ha sido entregado.'),
    ]
    current_index = next(
        (i for i, (s, _, _) in enumerate(status_steps) if s == order.status), 0
    )
    context = {
        'order': order,
        'status_steps': status_steps,
        'current_index': current_index,
    }
    return render(request, 'orders/order_tracking.html', context)
