def cart_context(request):
    context = {'cart_item_count': 0, 'cart_total': 0}
    try:
        from .models import Cart
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            sk = request.session.session_key
            if sk:
                cart = Cart.objects.filter(session_key=sk).first()
            else:
                cart = None
        if cart:
            context['cart_item_count'] = cart.total_items
            context['cart_total'] = cart.total
    except Exception:
        pass
    return context
