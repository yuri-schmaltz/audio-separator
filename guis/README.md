# UVR5 GUI (integrada)

Este diretório contém a **GUI oficial do Ultimate Vocal Remover 5 (UVR5)**,
**vendorizada** dentro deste repositório, para uso pessoal sem precisar instalar
separado.

## O que é a UVR5?

- **UVR5** é o projeto que **treina os modelos** (RoFormer, MDX-Net, VR, Demucs) que
  o `python-audio-separator` (CLI) usa internamente.
- Mantida por `@Anjok07` em https://github.com/Anjok07/ultimatevocalremovergui
- GUI em **Tkinter** (Python nativo) — funciona em Windows, macOS, Linux
- **Mesmo motor** do `audio-separator`, com casca gráfica para arrastar/visualizar

## Por que vendorizado?

| Opção | Trade-off |
|---|---|
| Submodule Git | requer `git clone --recursive`, branch detached, dor de cabeça |
| **Vendorizado (escolhido)** | `git clone` único resolve tudo, zero atrito |
| PyPI install | UVR5 não é publicado como pacote, só roda do source |

## Como rodar

### Linux / macOS / Windows (cross-platform, recomendado)
```bash
# Da raiz do repo:
python3 guis/run_gui.py
```

O script:
1. Detecta Python 3.10+
2. Detecta GPU NVIDIA via `nvidia-smi`
3. Cria venv dedicado em `.venv-uvr5/` (isolado do seu ambiente de dev)
4. Instala torch com CUDA 12.1 (GPU) ou CPU
5. Instala `requirements.txt` do UVR5
6. Instala `audio-separator[cpu]` (compat)
7. Avisa se faltar ffmpeg
8. Inicia a GUI

### Linux / macOS (Bash)
```bash
./guis/run-gui.sh
```

### Windows (cmd / PowerShell)
```cmd
guis\run-gui.bat
```

## Modelos

A GUI baixa modelos sob demanda pelo **Settings → Download Center**.
Modelos recomendados para 6 stems (vocals, bass, drums, guitar, piano, other):

| Modelo | Tamanho | SDR Vocals | SDR Bass | SDR Drums |
|---|---|---|---|---|
| **BS-Roformer-SW** (jarredou) | ~400 MB | 11.27 | 14.57 | 14.05 |
| `model_bs_roformer_ep_317_sdr_12.9755` | ~400 MB | 12.97 | n/d | n/d |
| `htdemucs_6s` (Demucs) | ~2.5 GB | 9.7 | 10.0 | 8.5 |

Para máxima qualidade: ative **Ensemble Mode** e combine 2-3 modelos.

## CLI também está aqui

A mesma engine funciona via CLI no diretório raiz do repo:
```bash
# Da raiz:
pip install "audio-separator[gpu]"
audio-separator musica.mp3 --model_filename BS-Roformer-SW.ckpt
```

## Onde os modelos são salvos?

A GUI UVR5 salva em:
- Windows: `%APPDATA%\UVR5\models\`
- macOS: `~/Library/Application Support/UVR5/models/`
- Linux: `~/.local/share/UVR5/models/`

O CLI audio-separator salva em `/tmp/audio-separator-models/` por padrão
(configurável com `--model_file_dir`).

**Os downloads NÃO são compartilhados** entre GUI e CLI — cada um usa seu
próprio cache. Para compartilhar, configure o mesmo `--model_file_dir` no CLI.

## Limitações conhecidas

- UVR5 tem **engines separados** do audio-separator (não compartilham cache
  de modelos nem código de inferência). Os modelos são os mesmos, mas o
  cache de downloads é duplicado.
- A GUI UVR5 só roda com Tkinter disponível. Em Linux server sem display,
  use só o CLI.
- A venv do UVR5 fica em `.venv-uvr5/` na raiz do repo (~3-5 GB com torch
  CUDA). Se espaço for problema, delete com `rm -rf .venv-uvr5`.

## Atualizando a UVR5 vendorizada

Periodicamente, o UVR5 recebe updates. Para atualizar:
```bash
# Do diretório raiz do repo:
cd guis/uvr5
git pull  # só funciona se você adicionou como submodule - vendorizado não
# Solução: re-vendorize
cd ../../
rm -rf guis/uvr5
git clone --depth 1 https://github.com/Anjok07/ultimatevocalremovergui.git guis/uvr5
rm -rf guis/uvr5/.git
git add guis/uvr5
git commit -m "chore: update UVR5 vendor"
```

## Créditos

- UVR5: [@Anjok07](https://github.com/Anjok07) + [@aufr33](https://github.com/aufr33)
  ([@Anjok07/ultimatevocalremovergui](https://github.com/Anjok07/ultimatevocalremovergui))
- Modelos: [@Anjok07](https://github.com/Anjok07), ViperX, Kimberley Jensen, unwa, Gabox,
  becruily, jarredou, frazer e muitos outros
- Wrapper CLI: [@beveradb](https://github.com/beveradb) (nomadkaraoke)
- Integração neste fork: [@yuri-schmaltz](https://github.com/yuri-schmaltz)
