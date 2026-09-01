@echo off
echo Instalando dependencias...
pip install -r requirements.txt

echo Gerando o executavel...
pyinstaller --onefile --windowed --name PCPulse dashboard.py

echo.
echo Pronto! O executavel esta em dist\PCPulse.exe
pause
