# Настройка

[English version](../setup.md)

## Требования

- Python 3.11 или новее
- [uv](https://docs.astral.sh/uv/)
- FFmpeg с `ffprobe` в `PATH` для определения длительности MP3, OGG, FLAC, M4A,
  AAC и Opus. Для WAV FFmpeg не требуется

## Установка

```bash
uv sync --extra whisper
```

Команда создаёт `.venv` и устанавливает `faster-whisper`, cuBLAS для CUDA 12 и
cuDNN 9. Модель Whisper скачается при обработке первого аудиофайла без субтитра.

## Настройка для платформы

Переводчик работает в Windows, macOS и Linux. Для транскрибатора также нужен
FFmpeg. GPU-транскрибация в проекте настроена для Linux с NVIDIA CUDA.

В примере для Windows используется CPU, потому что проект автоматически настраивает
пути к пакетным CUDA-библиотекам только в Linux. Транскрибацию на NVIDIA GPU можно
запустить и в Windows после самостоятельной настройки совместимых CUDA и CTranslate2,
но это выходит за пределы настройки проекта. В Linux пример использует GPU, потому
что при доступной NVIDIA CUDA это уже настроенный и более быстрый вариант.

### Windows

```powershell
winget install --id=astral-sh.uv -e
winget install --id=Gyan.FFmpeg.Shared -e
uv python install 3.12
uv sync --extra whisper
uv run deadlock-transcribe .\data\sources .\data\transcriptions --device cpu --compute-type int8
```

Установите Ollama с [ollama.com/download](https://ollama.com/download), затем:

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

Установите Ollama с [ollama.com/download](https://ollama.com/download), затем:

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions --language ru
```

### Linux

Команды рассчитаны на Debian и Ubuntu:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo apt update
sudo apt install ffmpeg
uv python install 3.12
uv sync --extra whisper
uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --model large-v3 --device cuda --compute-type float16
```

Для CPU используйте `--device cpu --compute-type int8`. Установите Ollama по
[инструкции для Linux](https://docs.ollama.com/linux), затем выполните:

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions --language ru
```

## Сервер Ollama

Переводчик обращается к `http://127.0.0.1:11434`.

- Windows и macOS: установите Ollama с [ollama.com/download](https://ollama.com/download).
  Приложение запускает сервер в фоне
- Linux: установите и запустите сервер:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

Оставьте `ollama serve` работающим в одном терминале, а переводчик запускайте в
другом. Если Ollama установлен как systemd-сервис, используйте
`sudo systemctl start ollama`.
