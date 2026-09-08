@echo off
REM Launcher para GUI UVR5 no Windows
REM Uso: run-gui.bat
setlocal enabledelayedexpansion

echo =======================================
echo   audio-separator - UVR5 GUI Launcher
echo =======================================
echo.

set SCRIPT_DIR=%~dp0
set UVR5_DIR=%SCRIPT_DIR%uvr5
set VENV_DIR=%SCRIPT_DIR%..\.venv-uvr5

REM Detectar Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.10+ antes.
    echo Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VERSION=%%v
echo [INFO] Python %PY_VERSION%

REM Verificar UVR5
if not exist "%UVR5_DIR%\UVR.py" (
    echo [ERRO] UVR5 nao encontrado em %UVR5_DIR%
    pause
    exit /b 1
)

REM Criar venv
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] Criando venv em %VENV_DIR%...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERRO] Falha ao criar venv
        pause
        exit /b 1
    )
)

REM Ativar venv
call "%VENV_DIR%\Scripts\activate.bat"

REM Atualizar pip
python -m pip install --quiet --upgrade pip

REM Detectar GPU NVIDIA
set HAS_GPU=0
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
    nvidia-smi >nul 2>&1
    if not errorlevel 1 set HAS_GPU=1
)

if "%HAS_GPU%"=="1" (
    echo [INFO] GPU NVIDIA detectada - instalando torch com CUDA 12.1
    python -m pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo [INFO] Sem GPU NVIDIA - instalando torch CPU
    python -m pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

REM Instalar deps UVR5
if exist "%UVR5_DIR%\requirements.txt" (
    echo [INFO] Instalando deps UVR5...
    python -m pip install --quiet -r "%UVR5_DIR%\requirements.txt"
)

REM Garantir audio-separator
python -m pip install --quiet "audio-separator[cpu]"

REM ffmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [AVISO] ffmpeg nao encontrado. Algumas funcionalidades podem falhar.
    echo Instale: https://ffmpeg.org/download.html#build-windows
)

REM Iniciar UVR5
echo.
echo [INFO] Iniciando UVR5 GUI...
echo        (feche a janela para encerrar)
echo.

cd /d "%UVR5_DIR%"
python UVR.py

endlocal
