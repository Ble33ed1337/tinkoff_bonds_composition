@echo off
chcp 65001 >nul
echo Запуск анализа состава портфеля через API Tinkoff...
echo Формат: $тикет; название; количество
cd /d "%~dp0"
C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe portfolio_api_composition.py
pause
