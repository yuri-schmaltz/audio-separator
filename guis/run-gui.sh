#!/usr/bin/env bash
# Launcher para GUI UVR5 (Ultimate Vocal Remover) integrada ao audio-separator
# Suporta: Linux, macOS, Windows (via Git Bash / WSL)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UVR5_DIR="$SCRIPT_DIR/uvr5"
VENV_DIR="$SCRIPT_DIR/../.venv-uvr5"

echo "🎵 audio-separator → UVR5 GUI launcher"
echo "======================================="

# Detectar Python
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "❌ Python não encontrado. Instale Python 3.10+ primeiro."
    exit 1
fi

PY_VERSION=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python $PY_VERSION"

# Verificar UVR5
if [ ! -f "$UVR5_DIR/UVR.py" ]; then
    echo "❌ UVR5 não encontrado em $UVR5_DIR"
    exit 1
fi

# Criar/ativar venv dedicado
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Criando venv em $VENV_DIR..."
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

# Ativar venv
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
else
    echo "❌ Falha ao ativar venv"
    exit 1
fi

# Instalar deps do UVR5
echo "📥 Verificando dependências UVR5..."
pip install --quiet --upgrade pip

# Instalar torch com CUDA se disponível (heurística simples)
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    echo "🎮 GPU NVIDIA detectada — instalando torch com CUDA 12.1"
    pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    echo "💻 Sem GPU NVIDIA detectada — instalando torch CPU"
    pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Deps UVR5 (preferir requirements-gui.txt com pins corrigidos para Python 3.12)
if [ -f "$SCRIPT_DIR/requirements-gui.txt" ]; then
    echo "📥 Instalando deps UVR5 (versão corrigida)..."
    pip install --quiet -r "$SCRIPT_DIR/requirements-gui.txt"
elif [ -f "$UVR5_DIR/requirements.txt" ]; then
    echo "📥 Instalando deps UVR5 (requirements.txt original — pode falhar em Python 3.12)..."
    pip install --quiet -r "$UVR5_DIR/requirements.txt"
fi

# Garantir deps do audio-separator instaladas (compat)
pip install --quiet "audio-separator[cpu]"

# ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "⚠️  ffmpeg não encontrado. Tentando instalar..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y ffmpeg || true
    elif command -v brew &>/dev/null; then
        brew install ffmpeg || true
    fi
fi

# Iniciar UVR5
echo ""
echo "🚀 Iniciando UVR5 GUI..."
echo "   (feche a janela para encerrar)"
echo ""

cd "$UVR5_DIR"
exec python UVR.py
