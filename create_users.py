import os, django
os.environ['DJANGO_SETTINGS_MODULE']='musicpro.settings'
django.setup()
from accounts.models import User, CustomerProfile

users_data = [
    {
        'username': 'admin',
        'email': 'admin@musicpro.cl',
        'first_name': 'Admin',
        'last_name': 'MusicPro',
        'user_type': 'admin',
        'is_staff': True,
        'is_superuser': True,
        'rut': '11.111.111-1',
        'password': 'admin123'
    },
    {
        'username': 'cliente1',
        'email': 'cliente@musicpro.cl',
        'first_name': 'Carlos',
        'last_name': 'Gonzalez',
        'user_type': 'customer',
        'rut': '22.222.222-2',
        'phone': '+56912345678',
        'address': 'Av. Libertador 1234',
        'city': 'Santiago',
        'region': 'Metropolitana',
        'postal_code': '7500000',
        'password': 'cliente123'
    },
    {
        'username': 'bodega1',
        'email': 'bodega@musicpro.cl',
        'first_name': 'Maria',
        'last_name': 'Torres',
        'user_type': 'warehouse',
        'rut': '33.333.333-3',
        'phone': '+56987654321',
        'password': 'bodega123'
    },
]

for u in users_data:
    pwd = u.pop('password')
    if not User.objects.filter(username=u['username']).exists():
        user = User.objects.create_user(password=pwd, **u)
        if u['user_type'] == 'customer':
            CustomerProfile.objects.create(user=user)
        print(f"Creado: {u['username']} / {pwd}")
    else:
        print(f"Ya existe: {u['username']}")
