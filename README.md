# PC Pulse [ Dashboard de Performance ]

App de monitoramento de CPU, RAM, disco e rede em tempo real, com
gráficos ao vivo. Interface escura (preto / azul / amarelo).

## Como gerar o .exe (no seu Windows)

Isso foi construído num ambiente Linux, e o PyInstaller só compila pro
sistema em que ele está rodando — por isso o .exe precisa ser gerado
direto no Windows. É rápido, 3 passos:

### 1. Instale o Python (se ainda não tiver)
Baixe em https://www.python.org/downloads/ (marque a opção "Add
Python to PATH" durante a instalação).

### 2. Abra o terminal (cmd ou PowerShell) nesta pasta e rode:

```
pip install -r requirements.txt
```

### 3. Gere o .exe com um clique duplo em `build.bat`

(ou rode manualmente: `pyinstaller --onefile --windowed --name PCPulse --icon=icon.ico dashboard.py`)

O executável final aparece em `dist\PCPulse.exe`. Pode copiar esse
arquivo pra onde quiser, ele roda sozinho, sem precisar do Python
instalado na máquina de destino.

## Rodando sem compilar (pra testar rápido)

```
pip install -r requirements.txt
python dashboard.py
```

## Estrutura

- `dashboard.py` — código do app (tkinter + psutil, sem dependências pesadas)
- `requirements.txt` — dependências (psutil, pyinstaller)
- `build.bat` — script de build pro Windows
