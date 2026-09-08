#!/usr/bin/env python3
"""
Cross-platform launcher for UVR5 GUI integrated with audio-separator.

Usage:
    python guis/run_gui.py
    python -m guis.run_gui
    # Ou via entry point (após install): audio-separator-gui
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
UVR5_DIR = SCRIPT_DIR / "uvr5"
VENV_DIR = SCRIPT_DIR.parent / ".venv-uvr5"
ENTRY = UVR5_DIR / "UVR.py"
# Preferir nosso requirements corrigido (compat Python 3.12)
# Fallback para o requirements original do UVR5 se o nosso sumir
REQ_FILE_LOCAL = SCRIPT_DIR / "requirements-gui.txt"
REQ_FILE_UVR5 = UVR5_DIR / "requirements.txt"
REQ_FILE = REQ_FILE_LOCAL if REQ_FILE_LOCAL.exists() else REQ_FILE_UVR5


def log(msg: str) -> None:
    print(msg, flush=True)


def die(msg: str, code: int = 1) -> None:
    log(f"[ERRO] {msg}")
    sys.exit(code)


def detect_python() -> str:
    """Retorna o python executável disponível."""
    for candidate in ("python3", "python"):
        path = shutil.which(candidate)
        if path:
            return path
    die("Python 3.10+ não encontrado. Instale antes de continuar.")


def detect_gpu() -> bool:
    """Detecta se há GPU NVIDIA disponível."""
    if not shutil.which("nvidia-smi"):
        return False
    try:
        result = subprocess.run(
            ["nvidia-smi"], capture_output=True, timeout=5, check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def venv_python() -> Path:
    """Retorna o path do python dentro do venv."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv(python: str) -> str:
    """Cria venv se necessário e retorna o python do venv."""
    vpy = venv_python()
    if not vpy.exists():
        log(f"[INFO] Criando venv em {VENV_DIR} ...")
        subprocess.run([python, "-m", "venv", str(VENV_DIR)], check=True)
    return str(vpy)


def pip_install(venv_py: str, packages: list[str], index_url: str | None = None) -> None:
    cmd = [venv_py, "-m", "pip", "install", "--quiet", "--upgrade", "pip"]
    subprocess.run(cmd, check=True)

    if index_url:
        cmd = [venv_py, "-m", "pip", "install", "--quiet", *packages, "--index-url", index_url]
    else:
        cmd = [venv_py, "-m", "pip", "install", "--quiet", *packages]
    subprocess.run(cmd, check=True)


def main() -> int:
    log("=" * 50)
    log("  audio-separator - UVR5 GUI launcher")
    log("=" * 50)
    log("")

    if not ENTRY.exists():
        die(f"UVR5 não encontrado em {UVR5_DIR}. "
            f"Verifique se o repo foi clonado completo.")

    python = detect_python()
    py_ver = subprocess.run(
        [python, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    log(f"[INFO] Python {py_ver}")

    # 3.10 mínimo (UVR5 tem libs que pedem isso)
    major, minor = map(int, py_ver.split("."))
    if (major, minor) < (3, 10):
        die(f"Python {py_ver} não suportado. Requer 3.10+.", code=2)

    has_gpu = detect_gpu()
    if has_gpu:
        log("[INFO] GPU NVIDIA detectada")
    else:
        log("[INFO] Sem GPU NVIDIA - usando CPU (mais lento)")

    venv_py = ensure_venv(python)

    # Instalar torch (GPU ou CPU)
    if has_gpu:
        log("[INFO] Instalando torch com CUDA 12.1 ...")
        pip_install(
            venv_py,
            ["torch", "torchvision", "torchaudio"],
            index_url="https://download.pytorch.org/whl/cu121",
        )
    else:
        log("[INFO] Instalando torch CPU ...")
        pip_install(
            venv_py,
            ["torch", "torchvision", "torchaudio"],
            index_url="https://download.pytorch.org/whl/cpu",
        )

    # Deps UVR5
    if REQ_FILE.exists():
        log("[INFO] Instalando deps UVR5 ...")
        pip_install(venv_py, ["-r", str(REQ_FILE)])

    # Garantir audio-separator
    log("[INFO] Garantindo audio-separator instalado ...")
    pip_install(venv_py, ["audio-separator[cpu]"])

    # ffmpeg
    if not shutil.which("ffmpeg"):
        log("[AVISO] ffmpeg não encontrado. Algumas features podem falhar.")
        log("        Linux:  sudo apt install ffmpeg")
        log("        macOS:  brew install ffmpeg")
        log("        Win:    https://ffmpeg.org/download.html#build-windows")

    # Iniciar UVR5
    log("")
    log("[INFO] Iniciando UVR5 GUI ...")
    log("       (feche a janela para encerrar)")
    log("")
    log("[DICA] Para usar o entry point 'audio-separator-gui' no PATH,")
    log("       rode:  pip install -e .  (na raiz do repo)")
    log("")

    os.chdir(str(UVR5_DIR))
    return subprocess.run([venv_py, str(ENTRY)]).returncode


if __name__ == "__main__":
    sys.exit(main())
