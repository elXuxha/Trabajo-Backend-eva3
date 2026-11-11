@echo off
title Music Pro - Instalacion
color 0A
echo.
echo  ==========================================
echo   Music Pro Tour 2026 - INSTALACION
echo  ==========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado.
    echo  Descarga desde: https://www.python.org/downloads/
    echo  Marca "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

echo [1/6] Creando entorno virtual...
python -m venv venv

echo [2/6] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [3/6] Instalando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Error al instalar dependencias.
    pause
    exit /b 1
)

echo [4/6] Aplicando migraciones...
python manage.py makemigrations accounts catalog cart orders warehouse admin_panel
python manage.py migrate
if %errorlevel% neq 0 (
    echo [ERROR] Error al aplicar migraciones.
    pause
    exit /b 1
)

echo [5/6] Generando datos ficticios con Faker...
python generate_fake_data.py

echo [6/6] Creando usuarios de prueba...
python create_users.py

echo.
echo  ==========================================
echo   INSTALACION COMPLETADA
echo  ==========================================
echo.
echo  Para iniciar: haz doble clic en "iniciar.bat"
echo  Diagrama BD:   abre "diagrama_bd.html"
echo.
pause
