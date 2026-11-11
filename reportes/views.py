"""
Panel de Reportes - Caso "TIENDA: Gestión Comercial, Clientes y Ventas".

Las 20 consultas del informe (documentos de la Evaluación 3) se resuelven
EXCLUSIVAMENTE con el ORM de Django: filter, values, annotate, aggregate,
Sum, Count, Avg, F, Q y TruncMonth.
No se usa SQL crudo: nada de .raw(), .extra(), cursor() ni connection.execute().

Mapeo de entidades del caso:
    Categoria  -> catalog.Category
    Producto   -> catalog.Product
    Cliente    -> accounts.User (user_type='customer')
    Venta      -> orders.Order
    DetalleVenta -> orders.OrderItem
"""
from datetime import date, datetime, timedelta, time
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.models import User
from catalog.models import Category, Product
from orders.models import Order, OrderItem


def staff_required(view_func):
    """Restringe los reportes a administradores. Siempre se usa bajo @login_required."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
            messages.error(request, 'No tienes acceso a los reportes de la tienda.')
            return redirect('catalog:home')
        return view_func(request, *args, **kwargs)
    return _wrapped


def _entero(valor, por_defecto):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return por_defecto


def _fecha(valor, por_defecto):
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return por_defecto


@login_required
@staff_required
def reportes_tienda(request):
    hoy = timezone.now().date()
    get = request.GET

    # ----- parámetros de los filtros (consultas con selección) -----
    anio = _entero(get.get('anio'), hoy.year)
    dia = _fecha(get.get('dia'), hoy)
    desde = _fecha(get.get('desde'), hoy - timedelta(days=30))
    hasta = _fecha(get.get('hasta'), hoy)
    precio_min = _entero(get.get('precio_min'), 0)
    precio_max = _entero(get.get('precio_max'), 0)

    categorias = Category.objects.filter(is_active=True)
    clientes = User.objects.filter(user_type='customer').order_by('first_name', 'username')
    ventas = Order.objects.select_related('user').order_by('-created_at')[:200]

    categoria_id = _entero(get.get('categoria'), categorias.first().id if categorias.exists() else 0)
    cliente_id = _entero(get.get('cliente'), clientes.first().id if clientes.exists() else 0)
    venta_id = _entero(get.get('venta'), ventas.first().id if ventas.exists() else 0)

    if not precio_max:
        precio_maximo = Product.objects.order_by('-price').values_list('price', flat=True).first()
        precio_max = int(precio_maximo) if precio_maximo else 9999990

    # Mes natural anterior (para la consulta 17: "último mes")
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_mes_inicio = (primer_dia_mes_actual - timedelta(days=1)).replace(day=1)
    ultimo_mes_fin = primer_dia_mes_actual

    # ================================================================
    #  NIVEL BÁSICO (consultas 1 a 5)
    # ================================================================
    # 1. ¿Cuáles son todos los productos disponibles en la tienda?
    q01_productos = Product.objects.filter(is_active=True).select_related('category', 'brand')

    # 2. ¿Qué productos pertenecen a una categoría seleccionada?
    q02_por_categoria = Product.objects.filter(
        is_active=True, category_id=categoria_id).select_related('category', 'brand')

    # 3. ¿Qué productos se encuentran dentro de un rango de precios?
    q03_rango_precios = Product.objects.filter(
        is_active=True, price__gte=precio_min, price__lte=precio_max
    ).select_related('category')

    # 4. ¿Cuáles son los 10 productos más caros de la tienda?
    q04_top_precio = Product.objects.filter(is_active=True).order_by('-price')[:10]

    # 5. ¿Cuántos clientes están registrados en el sistema?
    q05_total_clientes = User.objects.filter(user_type='customer').count()

    # ================================================================
    #  NIVEL INTERMEDIO (consultas 6 a 12)
    # ================================================================
    # 6. ¿Cuáles son las compras realizadas por un cliente específico?
    q06_compras_cliente = Order.objects.filter(
        user_id=cliente_id).select_related('user').order_by('-created_at')

    # 7. ¿Qué productos adquirió un cliente en una venta determinada?
    q07_productos_venta = OrderItem.objects.filter(
        order_id=venta_id).select_related('order', 'product')

    # 8. ¿Cuántas ventas se realizaron durante un período seleccionado?
    q08_ventas_periodo = Order.objects.filter(
        created_at__date__gte=desde, created_at__date__lte=hasta).select_related('user')
    q08_total_ventas = q08_ventas_periodo.count()
    q08_monto_periodo = q08_ventas_periodo.exclude(
        status='cancelled').aggregate(total=Sum('total'))['total'] or 0

    # 9. ¿Cuáles son los productos que tienen menos de cinco unidades disponibles?
    q09_poco_stock = Product.objects.filter(
        is_active=True, stock__lt=5).select_related('category')

    # 10. ¿Cuál es el monto total vendido durante un día seleccionado?
    q10_monto_dia = Order.objects.filter(
        created_at__date=dia).exclude(status='cancelled').aggregate(
        total=Sum('total'))['total'] or 0
    q10_ventas_dia = Order.objects.filter(created_at__date=dia).count()

    # 11. ¿Cuáles son los cinco productos más vendidos según cantidad de unidades?
    q11_top_unidades = (
        OrderItem.objects.values('product_id', 'product__name')
        .annotate(unidades=Sum('quantity'))
        .order_by('-unidades')[:5]
    )

    # 12. ¿Cuáles son los cinco clientes que han realizado más compras?
    q12_top_compradores = (
        User.objects.filter(user_type='customer')
        .annotate(compras=Count('orders'))
        .order_by('-compras')[:5]
    )

    # ================================================================
    #  NIVEL AVANZADO (consultas 13 a 17)
    # ================================================================
    # 13. ¿Cuál es el monto total comprado por cada cliente?
    q13_monto_por_cliente = (
        User.objects.filter(user_type='customer')
        .annotate(total_comprado=Sum('orders__total'))
        .order_by('-total_comprado')
    )

    # 14. ¿Qué productos nunca han sido vendidos?
    q14_nunca_vendidos = Product.objects.filter(
        orderitem__isnull=True).select_related('category')

    # 15. ¿Cuál es el promedio de dinero gastado por venta?
    q15_promedio_venta = Order.objects.exclude(status='cancelled').aggregate(
        promedio=Avg('total'))['promedio'] or 0

    # 16. ¿Qué categoría genera el mayor monto de ventas?
    q16_categoria_top = (
        OrderItem.objects.values('product__category__name')
        .annotate(monto=Sum(F('quantity') * F('product_price')))
        .order_by('-monto')[:1]
    )

    # 17. ¿Cuántas unidades se han vendido de cada producto durante el último mes?
    q17_unidades_mes = (
        OrderItem.objects.filter(
            order__created_at__date__gte=ultimo_mes_inicio,
            order__created_at__date__lt=ultimo_mes_fin)
        .values('product__name')
        .annotate(unidades=Sum('quantity'))
        .order_by('-unidades')
    )

    # ================================================================
    #  NIVEL ANÁLISIS (consultas 18 a 20)
    # ================================================================
    # 18. ¿Qué cliente ha gastado más dinero durante el año?
    q18_cliente_anio = (
        User.objects.filter(
            Q(user_type='customer') &
            Q(orders__created_at__year=anio) &
            ~Q(orders__status='cancelled'))
        .annotate(gasto=Sum('orders__total'))
        .order_by('-gasto').first()
    )

    # 19. ¿Cómo se distribuyen los montos de ventas por mes durante el año seleccionado?
    q19_montos_por_mes = (
        Order.objects.filter(created_at__year=anio).exclude(status='cancelled')
        .annotate(mes=TruncMonth('created_at'))
        .values('mes')
        .annotate(monto=Sum('total'), ventas=Count('id'))
        .order_by('mes')
    )

    # 20. ¿Cuáles son los 10 productos que generan mayores ingresos para la tienda?
    q20_top_ingresos = (
        OrderItem.objects.values('product_id', 'product__name')
        .annotate(ingresos=Sum(F('quantity') * F('product_price')))
        .order_by('-ingresos')[:10]
    )

    context = {
        # Básico
        'q01_productos': q01_productos,
        'q01_total': q01_productos.count(),
        'q02_por_categoria': q02_por_categoria,
        'q03_rango_precios': q03_rango_precios,
        'q04_top_precio': q04_top_precio,
        'q05_total_clientes': q05_total_clientes,
        # Intermedio
        'q06_compras_cliente': q06_compras_cliente,
        'q07_productos_venta': q07_productos_venta,
        'q08_ventas_periodo': q08_ventas_periodo,
        'q08_total_ventas': q08_total_ventas,
        'q08_monto_periodo': q08_monto_periodo,
        'q09_poco_stock': q09_poco_stock,
        'q10_monto_dia': q10_monto_dia,
        'q10_ventas_dia': q10_ventas_dia,
        'q11_top_unidades': q11_top_unidades,
        'q12_top_compradores': q12_top_compradores,
        # Avanzado
        'q13_monto_por_cliente': q13_monto_por_cliente,
        'q14_nunca_vendidos': q14_nunca_vendidos,
        'q15_promedio_venta': q15_promedio_venta,
        'q16_categoria_top': q16_categoria_top,
        'q17_unidades_mes': q17_unidades_mes,
        'q17_rango': {'desde': ultimo_mes_inicio, 'hasta': ultimo_mes_fin - timedelta(days=1)},
        # Análisis
        'q18_cliente_anio': q18_cliente_anio,
        'q19_montos_por_mes': q19_montos_por_mes,
        'q20_top_ingresos': q20_top_ingresos,
        # Auxiliares para los filtros
        'categorias': categorias,
        'clientes': clientes,
        'ventas': ventas,
        'filtros': {
            'categoria': categoria_id,
            'cliente': cliente_id,
            'venta': venta_id,
            'precio_min': precio_min,
            'precio_max': precio_max,
            'desde': desde.isoformat(),
            'hasta': hasta.isoformat(),
            'dia': dia.isoformat(),
            'anio': anio,
        },
        'fecha_reporte': timezone.now(),
    }
    return render(request, 'reportes_tienda.html', context)
