# Music Pro Tour 2026 — Tienda en Línea

Proyecto de comercio electrónico para **Music Pro S.A.**, caso *"Sucursales y Franquicias"*.

## Tecnologías

- **Backend:** Python / Django
- **Base de datos:** SQLite
- **Estilo:** Tailwind CSS (CDN)
- **Datos ficticios:** Faker

## Requisitos

- Python 3.10 o superior ([descargar](https://www.python.org/downloads/))
- Al instalar Python, marcar **"Add Python to PATH"**

---

## Instalación por primera vez

1. Copiar la carpeta del proyecto a la PC destino
2. Doble clic en **`instalar.bat`**
3. Esperar a que termine (instala dependencias, crea BD, genera datos con Faker)

## Iniciar la aplicación

1. Doble clic en **`iniciar.bat`**
2. Abrir el navegador en: **http://127.0.0.1:8000**

## Detener el servidor

Cerrar la ventana del servidor o presionar `Ctrl+C` dentro de ella.

---

## Credenciales

| Rol | Usuario | Contraseña | Acceso |
|-----|---------|------------|--------|
| Administrador | `admin` | `admin123` | `/admin/` y `/panel/` |
| Bodega | `bodega1` | `bodega123` | `/bodega/` |
| Cliente | `cliente1` | `cliente123` | Tienda y pedidos |

## URLs

| Página | URL |
|--------|-----|
| Tienda | http://127.0.0.1:8000/ |
| Django Admin | http://127.0.0.1:8000/admin/ |
| Panel Admin | http://127.0.0.1:8000/panel/ |
| Panel Bodega | http://127.0.0.1:8000/bodega/ |
| Registro | http://127.0.0.1:8000/cuenta/registro/ |
| Login | http://127.0.0.1:8000/cuenta/login/ |
| Diagrama BD | Abrir `diagrama_bd.html` en el navegador |

---

## Archivos importantes

| Archivo | Función |
|---------|---------|
| `instalar.bat` | Instalación automática (primera vez) |
| `iniciar.bat` | Inicia el servidor de desarrollo |
| `manage.py` | Comandos de Django |
| `requirements.txt` | Dependencias del proyecto |
| `generate_fake_data.py` | Genera datos ficticios con Faker |
| `create_users.py` | Crea usuarios de prueba |
| `diagrama_bd.html` | Diagrama de base de datos |
| `verify_e1.py` | Verifica datos y configuración |

## Estructura del proyecto

```
Trabajo Backend/
├── musicpro/          Configuración (settings, urls, wsgi)
├── accounts/          Usuarios y perfiles
├── catalog/           Productos, categorías, marcas, sucursales
├── cart/              Carrito de compras
├── orders/            Pedidos y despachos
├── warehouse/         Panel de bodega
├── admin_panel/       Panel de administración
├── templates/         Vistas HTML (Tailwind CSS)
├── static/            Archivos estáticos
├── media/             Imágenes subidas
├── db.sqlite3         Base de datos
├── diagrama_bd.html   Diagrama ER
├── instalar.bat       Instalación
└── iniciar.bat        Inicio del servidor
```

## Comandos útiles

```bash
# Activar entorno virtual
venv\Scripts\activate

# Crear migraciones (si se modifican modelos)
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Generar datos ficticios
python generate_fake_data.py

# Crear superusuario manualmente
python manage.py createsuperuser

# Verificar configuración
python manage.py check
```
