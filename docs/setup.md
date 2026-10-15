# Setup

[Русская версия](./ru/setup.md)

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- FFmpeg with `ffprobe` in `PATH` for MP3, OGG, FLAC, M4A, AAC, and Opus duration
  detection. WAV files do not require FFmpeg

## Install

```bash
uv sync --extra whisper
```

This creates `.venv` and installs `faster-whisper`, CUDA 12 cuBLAS, and cuDNN 9.
The Whisper model is downloaded when the first audio file without a subtitle is
processed.

## Platform setup

The translator works on Windows, macOS, and Linux. Transcription also needs FFmpeg.
GPU transcription in this project is configured for Linux with NVIDIA CUDA.

The Windows example uses CPU because the project automatically configures the
packaged CUDA runtime libraries only on Linux. A compatible CUDA and CTranslate2
setup can also use an NVIDIA GPU on Windows, but its setup is outside this project.
The Linux example uses GPU because it is the configured, faster option when NVIDIA
CUDA is available.

### Windows

```powershell
winget install --id=astral-sh.uv -e
winget install --id=Gyan.FFmpeg.Shared -e
uv python install 3.12
uv sync --extra whisper
uv run deadlock-transcribe .\data\sources .\data\transcriptions --device cpu --compute-type int8
```

Install Ollama from [ollama.com/download](https://ollama.com/download), then run:

```powershell
ollama pull qwen2.5:7b
uv run deadlock-translate .\data\transcriptions --language ru
```

### macOS

```bash
brew install uv ffmpeg
uv python install 3.12
uv sync --extra whisper
uv run deadlock-transcribe ./data/sources ./data/transcriptions --device cpu --compute-type int8
```

Install Ollama from [ollama.com/download](https://ollama.com/download), then run:

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions --language ru
```

### Linux

These commands target Debian and Ubuntu systems:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo apt update
sudo apt install ffmpeg
uv python install 3.12
uv sync --extra whisper
uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --model large-v3 --device cuda --compute-type float16
```

For CPU transcription, use `--device cpu --compute-type int8` instead. Install
Ollama with its [Linux instructions](https://docs.ollama.com/linux), then run:

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions --language ru
```

## Ollama server

The translator connects to `http://127.0.0.1:11434`.

- Windows and macOS: install Ollama from [ollama.com/download](https://ollama.com/download).
  The application starts the server in the background
- Linux: install and start the server:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

Keep `ollama serve` running in one terminal while using the translator from another.
When Ollama is a systemd service, start it with `sudo systemctl start ollama`.
