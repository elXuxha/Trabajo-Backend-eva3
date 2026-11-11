@echo off
title Music Pro - Servidor
color 0B
echo.
echo  ==========================================
echo   Music Pro Tour 2026 - Iniciando...
echo  ==========================================
echo.

call venv\Scripts\activate.bat

echo  Servidor iniciando en http://127.0.0.1:8000
echo  Presiona Ctrl+C para detener.
echo.
echo  ------------------------------------------
echo   CREDENCIALES:
echo   Admin:   admin / admin123
echo   Bodega:  bodega1 / bodega123
echo   Cliente: cliente1 / cliente123
echo  ------------------------------------------
echo.

python manage.py runserver 0.0.0.0:8000

pause
