from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Cart, CartItem
from catalog.models import Product


def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    if request.method != 'POST':
        return redirect('catalog:product_detail', slug=product.slug)
    
    if not product.is_in_stock:
        messages.error(request, 'Este producto no está disponible.')
        return redirect('catalog:product_detail', slug=product.slug)
    
    cart = get_cart(request)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
    
    if quantity < 1:
        quantity = 1
    
    if quantity > product.stock:
        messages.warning(request, f'Solo hay {product.stock} unidades disponibles.')
        quantity = product.stock
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
        if cart_item.quantity > product.stock:
            cart_item.quantity = product.stock
            messages.warning(request, f'Se ajustó la cantidad al stock disponible ({product.stock}).')
    else:
        cart_item.quantity = quantity
    cart_item.save()
    
    messages.success(request, f'{product.name} agregado al carrito.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'total_items': cart.total_items,
            'total': float(cart.total),
            'message': f'{product.name} agregado al carrito.'
        })
    
    return redirect('cart:cart_detail')


def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = get_cart(request)
    if cart_item.cart == cart:
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} eliminado del carrito.')
    return redirect('cart:cart_detail')


def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = get_cart(request)
    if cart_item.cart == cart:
        if request.method != 'POST':
            return redirect('cart:cart_detail')
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
        
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, 'Item eliminado del carrito.')
        elif quantity > cart_item.product.stock:
            cart_item.quantity = cart_item.product.stock
            cart_item.save()
            messages.warning(request, f'Se ajustó al stock disponible ({cart_item.product.stock}).')
        else:
            cart_item.quantity = quantity
            cart_item.save()
    return redirect('cart:cart_detail')


def cart_detail_view(request):
    cart = get_cart(request)
    items = cart.items.select_related('product').all()
    context = {
        'cart': cart,
        'items': items,
        'subtotal': cart.total,
        'shipping': cart.shipping_cost,
        'grand_total': cart.total + cart.shipping_cost,
    }
    return render(request, 'cart/cart_detail.html', context)


def cart_count_api(request):
    cart = get_cart(request)
    return JsonResponse({
        'total_items': cart.total_items,
        'total': float(cart.total),
    })
