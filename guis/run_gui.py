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


def check_system_tkinter() -> None:
    """Verifica tkinter no Python do SISTEMA (não do venv).
    Se faltar, tenta instalar via apt (com sudo).
    """
    system_python = shutil.which("python3") or shutil.which("python")
    if not system_python:
        return

    result = subprocess.run(
        [system_python, "-c", "import tkinter"],
        capture_output=True, check=False,
    )
    if result.returncode == 0:
        log("[CHECK] tkinter OK no Python do sistema")
        return

    # tkinter ausente — tentar instalar via apt
    log("[CHECK] tkinter AUSENTE no sistema (Python não consegue importar)")
    if platform.system() != "Linux":
        log(f"[AVISO] Sistema {platform.system()} detectado. Instale python-tk manualmente.")
        return

    if not shutil.which("apt-get") and not shutil.which("apt"):
        log("[AVISO] apt nao encontrado. Instale python3-tk manualmente.")
        return

    # Tentar instalar sem sudo primeiro (caso ja tenha permissao)
    pkg_managers = []
    if shutil.which("apt-get"):
        pkg_managers.append("apt-get")
    if shutil.which("apt"):
        pkg_managers.append("apt")

    cmd = None
    for pm in pkg_managers:
        # Detectar versao do python
        py_ver = subprocess.run(
            [system_python, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        major, minor = py_ver.split(".")
        candidate_pkgs = [
            f"python3-tk",
            f"python{major}.{minor}-tk",
            "python3-dev",
        ]
        cmd = [pm, "install", "-y"] + candidate_pkgs
        break

    if not cmd:
        log("[AVISO] Nao foi possivel construir comando de instalacao. Instale python3-tk manualmente.")
        return

    log(f"[FIX] Tentando instalar via {' '.join(cmd)} (vai pedir senha sudo) ...")
    try:
        subprocess.run(["sudo", "-n"] + cmd, check=False)
        # Se sudo -n falhou (precisa de senha), tentar interativo
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            log("[FIX] tkinter instalado com sucesso!")
        else:
            log(f"[AVISO] Falha ao instalar tkinter (rc={result.returncode}).")
            log("        Rode manualmente:  sudo apt install -y python3-tk python3-dev")
    except Exception as e:
        log(f"[AVISO] Erro: {e}")
        log("        Rode manualmente:  sudo apt install -y python3-tk python3-dev")


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
    """Instala pacotes. Se receber lista com 1 item, raise se falhar. Se múltiplos, pula o que falhar."""
    # upgrade pip primeiro (sempre)
    subprocess.run(
        [venv_py, "-m", "pip", "install", "--quiet", "--upgrade", "pip", "wheel", "setuptools"],
        check=True,
    )

    if index_url:
        cmd_template = lambda pkg: [venv_py, "-m", "pip", "install", "--quiet", pkg, "--index-url", index_url]
    else:
        cmd_template = lambda pkg: [venv_py, "-m", "pip", "install", "--quiet", pkg]

    # Se for requirements file (-r path), instala tudo de uma vez e aborta se falhar
    if len(packages) == 1 and packages[0].startswith("-r"):
        cmd = [venv_py, "-m", "pip", "install", "--quiet", *packages]
        subprocess.run(cmd, check=True)
        return

    # Lista de pacotes soltos: instala um a um, pula falhas
    failed = []
    for pkg in packages:
        try:
            subprocess.run(cmd_template(pkg), check=True, capture_output=False)
        except subprocess.CalledProcessError:
            log(f"[AVISO] Falhou: {pkg} (continuando...)")
            failed.append(pkg)

    if failed:
        log(f"[AVISO] {len(failed)} pacote(s) nao instalado(s): {', '.join(failed)}")
        log("        A GUI pode nao funcionar completamente. Veja TROUBLESHOOTING_GUI.md")


def pip_install_file(venv_py: str, req_file: Path, index_url: str | None = None) -> None:
    """Instala um arquivo requirements.txt pacote por pacote, pulando falhas."""
    if not req_file.exists():
        log(f"[AVISO] requirements nao encontrado: {req_file}")
        return

    # upgrade pip + wheel + setuptools primeiro
    subprocess.run(
        [venv_py, "-m", "pip", "install", "--quiet", "--upgrade", "pip", "wheel", "setuptools"],
        check=True,
    )

    failed = []
    with open(req_file) as f:
        for raw in f:
            line = raw.strip()
            # pular linhas vazias
            if not line:
                continue
            # pular comentários full-line
            if line.startswith("#"):
                continue
            # pular flags especiais (-r, -e, --index-url, etc)
            if line.startswith("-"):
                continue
            # IMPORTANTE: strip comentários inline (# ...) e env markers (; ...)
            # 'audioread>=3.0.1  # comentario' → 'audioread>=3.0.1'
            # 'numpy>=1.26 ; python_version<"3.12"' → 'numpy>=1.26'
            pkg = line.split("#", 1)[0].split(";", 1)[0].strip()
            if not pkg:
                continue
            try:
                if index_url:
                    subprocess.run(
                        [venv_py, "-m", "pip", "install", "--quiet", pkg, "--index-url", index_url],
                        check=True,
                    )
                else:
                    subprocess.run(
                        [venv_py, "-m", "pip", "install", "--quiet", pkg],
                        check=True,
                    )
            except subprocess.CalledProcessError:
                log(f"[AVISO] Falhou: {pkg} (pulando)")
                failed.append(pkg)

    if failed:
        log("")
        log(f"[RESUMO] {len(failed)} pacote(s) nao instalado(s):")
        for f in failed:
            log(f"   - {f}")
        log("         A GUI pode nao funcionar completamente. Tente instalar manualmente:")
        log("         pip install <pacote>")


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

    # Verificar tkinter no SISTEMA (antes de instalar deps)
    check_system_tkinter()

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

    # Deps UVR5 (instala pacote por pacote, pula falhas)
    if REQ_FILE.exists():
        log(f"[INFO] Instalando deps UVR5 de {REQ_FILE.name} ...")
        pip_install_file(venv_py, REQ_FILE)

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

    # Validação pré-startup: tkinter e display
    log("[CHECK] Validando tkinter e display ...")
    precheck = subprocess.run(
        [venv_py, "-c", "import tkinter; import os; print('DISPLAY' in os.environ or os.name == 'nt')"],
        capture_output=True, text=True,
    )
    if precheck.returncode != 0:
        log("")
        log("╔══════════════════════════════════════════════════════════════╗")
        log("║  ERRO: tkinter nao disponivel no Python do venv              ║")
        log("╚══════════════════════════════════════════════════════════════╝")
        log("")
        log("Causa provavel: python3-tk nao instalado no sistema.")
        log("O Python 3.12 do Ubuntu 24.04+ / Debian 12+ separa o tkinter")
        log("em um pacote de sistema. Instale com:")
        log("")
        log("    sudo apt install -y python3-tk python3-dev")
        log("")
        log("Depois rode o launcher de novo.")
        return 1

    has_display = "True" in precheck.stdout
    if not has_display:
        log("")
        log("╔══════════════════════════════════════════════════════════════╗")
        log("║  ERRO: nenhuma sessao de display disponivel                  ║")
        log("╚══════════════════════════════════════════════════════════════╝")
        log("")
        log("A GUI UVR5 precisa de um servidor grafico (X11/Wayland).")
        log("Voce esta em:")
        log("  - SSH sem X forwarding? Conecte com 'ssh -X user@host'")
        log("  - Container/headless? Use o CLI: audio-separator (sem GUI)")
        log("  - Wayland? Instale xwayland")
        return 1

    log("[CHECK] OK")
    log("")
    log("[DICA] Para usar o entry point 'audio-separator-gui' no PATH,")
    log("       rode:  pip install -e .  (na raiz do repo)")
    log("")

    os.chdir(str(UVR5_DIR))
    return subprocess.run([venv_py, str(ENTRY)]).returncode


if __name__ == "__main__":
    sys.exit(main())
