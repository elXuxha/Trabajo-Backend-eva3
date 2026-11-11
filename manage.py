import os, sys
from faker import Faker

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicpro.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Asegurate de tener Python y un entorno virtual creado."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()


