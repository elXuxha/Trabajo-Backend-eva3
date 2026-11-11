"""
Inyección masiva de datos (stress) para Music Pro.

Uso:
    python manage.py inyectar_stress
    python manage.py inyectar_stress --usuarios 5000 --productos 2000 --pedidos 20000

Optimizaciones exigidas por la rúbrica:
  * PRAGMAs de SQLite (synchronous = OFF, journal_mode = MEMORY) antes de inyectar.
  * bulk_create con batch_size=1000 envuelto en transaction.atomic().
  * make_password() calculado UNA sola vez, fuera de los bucles.
  * Faker llamado una sola vez para construir "pools" (listas cacheadas);
    dentro de los bucles sólo se usa random.choice() / random.choices().
"""
import random
import time
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from django.utils.text import slugify

from faker import Faker

from accounts.models import CustomerProfile, User
from catalog.models import Brand, Category, Product
from orders.models import Order, OrderItem

fake = Faker('es_CL')
Faker.seed(42)
random.seed(42)

BATCH_SIZE = 1000        # bulk_create(batch_size=1000)
CHUNK = 500              # máx. de valores por consulta IN
DIAS_HISTORIAL = 365     # antigüedad con la que se reparten las fechas

# ---------------------------------------------------------------------------
# Pools estáticos (se construyen una sola vez, fuera de los bucles)
# ---------------------------------------------------------------------------
CATEGORIAS = [
    'Guitarras', 'Guitarras Electricas', 'Guitarras Acusticas', 'Teclados y Pianos',
    'Baterias y Percusion', 'Audio Profesional', 'Equipos DJ', 'Accesorios',
    'Percusion Latino', 'Estudio y Produccion',
]

MARCAS = [
    'Fender', 'Gibson', 'Yamaha', 'Roland', 'Pioneer DJ', 'Shure', 'Ibanez',
    'Music Pro', 'Behringer', 'Casio', 'Tama', 'Zildjian', 'Pearl', 'Korg',
]

REGIONES = [
    'Arica y Parinacota', 'Tarapaca', 'Antofagasta', 'Atacama', 'Coquimbo',
    'Valparaiso', 'Metropolitana', 'Libertador', 'Maule', 'Nuble', 'Biobio',
    'Araucania', 'Los Rios', 'Los Lagos', 'Aysen', 'Magallanes',
]

TIPOS = [
    'Guitarra Electrica', 'Guitarra Acustica', 'Bajo', 'Teclado Digital',
    'Piano', 'Bateria', 'Cajon', 'Micrófono', 'Mezcladora', 'Controlador DJ',
    'Tornamesa', 'Parlante', 'Amplificador', 'Auriculares', 'Cuerdas', 'Funda',
]

MODELOS = [
    'Player', 'Standard', 'Custom', 'Premium', 'Pro', 'Studio', 'Live',
    'Vintage', 'Edition', 'Signature', 'Compact', 'Deluxe', 'MK II', 'X',
]

FRASES = [
    'Sonido profesional listo para el escenario y el estudio.',
    'Construcción robusta con acabados de alta gama.',
    'Ideal para músicos exigentes y productores creativos.',
    'Respuesta precisa y gran definición en cada nota.',
    'Equipado con componentes seleccionados y garantía local.',
    'Diseño ergonómico para sesiones largas de práctica.',
    'Prestaciones superiores a un precio accesible.',
    'Un clásico renovado con tecnología contemporánea.',
]

PRECIOS = [
    '9990', '14990', '19990', '24990', '34990', '49990', '79990', '99990',
    '149990', '199990', '249990', '349990', '449990', '649990', '899990',
    '1299990', '1799990',
]

STOCK_POOL = [0, 0, 1, 2, 3, 4, 5, 5, 8, 12, 20, 35, 50, 80, 120, 200]

ESTADOS = ['pending', 'confirmed', 'processing', 'shipped', 'in_transit', 'delivered', 'cancelled']
ESTADOS_PESOS = [25, 15, 12, 12, 6, 25, 5]
PAGOS = ['credit_card', 'debit_card', 'transfer', 'webpay', 'mercadopago']
DESPACHOS = ['home', 'pickup', 'express']
ENVIOS = [Decimal('0'), Decimal('4990'), Decimal('9990'), Decimal('12990')]


class Command(BaseCommand):
    help = 'Inyección masiva de datos (stress): usuarios, productos, pedidos e items.'

    def add_arguments(self, parser):
        parser.add_argument('--usuarios', type=int, default=5000)
        parser.add_argument('--productos', type=int, default=2000)
        parser.add_argument('--pedidos', type=int, default=20000)

    # ------------------------------------------------------------------ utils
    @staticmethod
    def _pk_por_campo(modelo, campo, valores):
        """Recupera los pks generados por bulk_create en fragmentos de CHUNK."""
        pks = {}
        for i in range(0, len(valores), CHUNK):
            fragmento = valores[i:i + CHUNK]
            for obj in modelo.objects.filter(**{f'{campo}__in': fragmento}):
                pks[getattr(obj, campo)] = obj.pk
        return pks

    @staticmethod
    def _construir_pools():
        """Faker se invoca UNA sola vez aquí; después sólo random.choice()."""
        return {
            'nombres': [fake.first_name() for _ in range(300)],
            'apellidos': [fake.last_name() for _ in range(300)],
            'calles': [fake.street_address() for _ in range(500)],
            'ciudades': [fake.city() for _ in range(150)],
            'telefonos': [f'+56 9 {random.randint(10000000, 99999999)}' for _ in range(400)],
            'frases': list(FRASES) + [fake.sentence(nb_words=10) for _ in range(300)],
            'precios': [Decimal(p) for p in PRECIOS],
            'stock': list(STOCK_POOL),
            'tipos': list(TIPOS),
            'modelos': list(MODELOS),
            'regiones': list(REGIONES),
            'pagos': list(PAGOS),
            'despachos': list(DESPACHOS),
            'envios': list(ENVIOS),
        }

    def _distribuir_fechas(self, modelo, objetos):
        """Reparte created_at/updated_at en los últimos 12 meses usando sólo el ORM (update)."""
        objetos = [o for o in objetos if o.pk]
        if not objetos:
            return
        hoy = timezone.now()
        total = len(objetos)
        grupos = {}
        for i, obj in enumerate(objetos):
            desfase = (i * DIAS_HISTORIAL) // total          # 0 .. 364
            fecha = hoy - timedelta(days=desfase, hours=(i % 23), minutes=(i % 59), seconds=(i % 59))
            grupos.setdefault(desfase, []).append((obj.pk, fecha))

        for registros in grupos.values():
            fecha = registros[0][1]
            pks = [pk for pk, _ in registros]
            for i in range(0, len(pks), CHUNK):
                modelo.objects.filter(pk__in=pks[i:i + CHUNK]).update(
                    created_at=fecha, updated_at=fecha)

    # ------------------------------------------------------------- inyectores
    def _inyectar_categorias(self):
        existentes = set(Category.objects.values_list('name', flat=True))
        nuevas = [
            Category(name=nombre, slug=slugify(nombre),
                     description=f'Categoría {nombre}', is_active=True)
            for nombre in CATEGORIAS if nombre not in existentes
        ]
        if nuevas:
            Category.objects.bulk_create(nuevas, batch_size=BATCH_SIZE, ignore_conflicts=True)
        return list(Category.objects.filter(name__in=CATEGORIAS))

    def _inyectar_marcas(self):
        existentes = set(Brand.objects.values_list('name', flat=True))
        nuevas = [
            Brand(name=nombre, slug=slugify(nombre), is_active=True)
            for nombre in MARCAS if nombre not in existentes
        ]
        if nuevas:
            Brand.objects.bulk_create(nuevas, batch_size=BATCH_SIZE, ignore_conflicts=True)
        return list(Brand.objects.filter(name__in=MARCAS))

    def _inyectar_productos(self, cantidad, categorias, marcas, pools):
        productos = []
        for i in range(cantidad):
            marca = random.choice(marcas) if marcas else None
            tipo = random.choice(pools['tipos'])
            modelo = random.choice(pools['modelos'])
            nombre = f'{marca.name if marca else "Music Pro"} {tipo} {modelo}'
            precio = random.choice(pools['precios'])
            en_oferta = random.choice([True, False])
            productos.append(Product(
                name=nombre,
                slug=f'{slugify(nombre)[:80]}-{i}',
                sku=f'STR-{i:06d}',
                description=f'{nombre}. {random.choice(pools["frases"])}',
                short_description=random.choice(pools['frases'])[:120],
                price=precio,
                original_price=(precio * Decimal('1.25')) if en_oferta else None,
                category=random.choice(categorias),
                brand=marca,
                stock=random.choice(pools['stock']),
                min_stock=random.choice([3, 5, 8, 10]),
                is_active=True,
                is_featured=random.choice([True, False]),
                is_new=random.choice([True, False]),
                is_on_sale=en_oferta,
            ))
        Product.objects.bulk_create(productos, batch_size=BATCH_SIZE, ignore_conflicts=True)

        pks = self._pk_por_campo(Product, 'sku', [p.sku for p in productos])
        productos = [p for p in productos if pks.get(p.sku)]
        for p in productos:
            p.pk = pks[p.sku]
        return productos

    def _inyectar_usuarios(self, cantidad, password_hash, pools):
        usuarios = []
        for i in range(cantidad):
            username = f'stress{i:06d}'
            base = 20000000 + i
            usuarios.append(User(
                username=username,
                email=f'{username}@mail.cl',
                first_name=random.choice(pools['nombres']),
                last_name=random.choice(pools['apellidos']),
                password=password_hash,          # hash calculado FUERA del bucle
                user_type='customer',
                is_active=True,
                phone=random.choice(pools['telefonos']),
                address=random.choice(pools['calles']),
                city=random.choice(pools['ciudades']),
                region=random.choice(pools['regiones']),
                postal_code=str(random.randint(1000000, 9999999)),
                rut=f'{base // 100}.{base % 100:02d}-{(i % 9) + 1}',
            ))
        User.objects.bulk_create(usuarios, batch_size=BATCH_SIZE, ignore_conflicts=True)

        pks = self._pk_por_campo(User, 'username', [u.username for u in usuarios])
        usuarios = [u for u in usuarios if pks.get(u.username)]
        for u in usuarios:
            u.pk = pks[u.username]

        perfiles = [
            CustomerProfile(user=u, loyalty_points=random.randint(0, 500),
                            newsletter_subscribed=random.choice([True, False]))
            for u in usuarios
        ]
        CustomerProfile.objects.bulk_create(perfiles, batch_size=BATCH_SIZE, ignore_conflicts=True)
        return usuarios

    def _inyectar_pedidos(self, cantidad, usuarios, productos, pools):
        if not usuarios or not productos:
            self.stdout.write('Sin usuarios o productos disponibles: se omiten los pedidos.')
            return []

        preparados = []
        for i in range(cantidad):
            usuario = random.choice(usuarios)
            elegidos = random.sample(productos, min(random.randint(1, 4), len(productos)))
            subtotal = Decimal('0')
            detalle = []
            for producto in elegidos:
                unidades = random.randint(1, 3)
                subtotal += producto.price * unidades
                detalle.append((producto, unidades))

            envio = random.choice(pools['envios'])
            orden = Order(
                order_number=f'MPSTR{i:09d}',
                user=usuario,
                status=random.choices(ESTADOS, weights=ESTADOS_PESOS, k=1)[0],
                payment_method=random.choice(pools['pagos']),
                shipping_method=random.choice(pools['despachos']),
                shipping_name=f'{usuario.first_name} {usuario.last_name}',
                shipping_address=random.choice(pools['calles']),
                shipping_city=random.choice(pools['ciudades']),
                shipping_region=random.choice(pools['regiones']),
                shipping_postal_code=str(random.randint(1000000, 9999999)),
                shipping_phone=random.choice(pools['telefonos']),
                subtotal=subtotal,
                shipping_cost=envio,
                discount=Decimal('0'),
                total=subtotal + envio,
                notes=random.choice(pools['frases']),
            )
            preparados.append((orden, detalle))

        ordenes = [o for o, _ in preparados]
        Order.objects.bulk_create(ordenes, batch_size=BATCH_SIZE, ignore_conflicts=True)

        pks = self._pk_por_campo(Order, 'order_number', [o.order_number for o in ordenes])
        items = []
        for orden, detalle in preparados:
            orden.pk = pks.get(orden.order_number)
            if not orden.pk:
                continue
            for producto, unidades in detalle:
                items.append(OrderItem(
                    order=orden,
                    product=producto,
                    product_name=producto.name,
                    product_price=producto.price,
                    quantity=unidades,
                ))
        OrderItem.objects.bulk_create(items, batch_size=BATCH_SIZE, ignore_conflicts=True)

        self._distribuir_fechas(Order, ordenes)
        return ordenes

    # ---------------------------------------------------------------- handle
    def handle(self, *args, **options):
        inicio = time.monotonic()

        # 1) PRAGMAs de SQLite ANTES de inyectar datos
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA synchronous = OFF;')
            cursor.execute('PRAGMA journal_mode = MEMORY;')

        # 2) Hash de contraseña calculado UNA vez, fuera de los bucles
        password_hash = make_password('stress123')

        # 3) Pools cacheados: Faker se ejecuta fuera de los bucles
        pools = self._construir_pools()

        with transaction.atomic():
            categorias = self._inyectar_categorias()
            marcas = self._inyectar_marcas()

            productos = self._inyectar_productos(options['productos'], categorias, marcas, pools)
            usuarios = self._inyectar_usuarios(options['usuarios'], password_hash, pools)
            self._distribuir_fechas(User, usuarios)

            clientes = list(User.objects.filter(user_type='customer'))
            ordenes = self._inyectar_pedidos(
                options['pedidos'],
                clientes if clientes else usuarios,
                productos, pools,
            )

        elapsed = time.monotonic() - inicio
        self.stdout.write(self.style.SUCCESS(
            f'Inyeccion completada en {elapsed:.1f}s - '
            f'{Product.objects.count()} productos - '
            f'{User.objects.filter(user_type="customer").count()} clientes · '
            f'{Order.objects.count()} pedidos · '
            f'{OrderItem.objects.count()} items.'
        ))
