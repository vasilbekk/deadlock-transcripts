# Deadlock Transcripts: ready-to-use tools for automatic transcription and translation

[🇷🇺 Перевод документации на русский язык](./docs/README.ru.md)

This repository contains multilanguage transcriptions for every voice line of every
Deadlock hero. You can add more languages locally by running
`deadlock-translate` with a local Ollama model on your GPU.

## Languages

- English (`en`)
- Russian (`ru`)

`deadlock-transcriber` provides command-line tools for building and extending the
catalogue. `deadlock-transcribe` uses extracted game assets and a local Whisper
model. `deadlock-translate` adds translations with local Ollama models and
available official game localizations.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- FFmpeg with `ffprobe` in `PATH` for MP3, OGG, FLAC, M4A, AAC, and Opus duration
  detection. WAV files do not require FFmpeg.

## Install

```bash
uv sync --extra whisper
```

This creates `.venv` and installs `faster-whisper`, CUDA 12 cuBLAS, and cuDNN 9.
On Linux, the command configures the packaged CUDA library paths automatically
before starting Whisper. The model is downloaded when the first audio file without
a subtitle is processed.

## Platform setup

The translator works on Windows, macOS, and Linux. Transcription also needs
FFmpeg. GPU transcription in this project is configured for Linux with NVIDIA CUDA;
use CPU mode on Windows and macOS unless you have set up a supported CTranslate2
backend yourself.

### Windows

Run these commands in PowerShell from the project directory:

```powershell
winget install --id=astral-sh.uv -e
winget install --id=Gyan.FFmpeg.Shared -e
uv python install 3.12
uv sync --extra whisper
```

For CPU transcription:

```powershell
uv run deadlock-transcribe .\data\sources .\data\transcriptions --device cpu --compute-type int8
```

Install Ollama from [ollama.com/download](https://ollama.com/download), then pull a
translation model:

```powershell
ollama pull qwen2.5:7b
uv run deadlock-translate .\data\transcriptions --language ru
```

### macOS

Install Homebrew first if it is not already available, then run:

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

The following commands target Debian and Ubuntu systems:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo apt update
sudo apt install ffmpeg
uv python install 3.12
uv sync --extra whisper
```

For NVIDIA CUDA transcription:

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --model large-v3 --device cuda --compute-type float16
```

For CPU transcription, replace the last command's device settings with
`--device cpu --compute-type int8`. Install Ollama with its
[Linux instructions](https://docs.ollama.com/linux), then pull and run Qwen:

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions --language ru
```

## Ollama installation and startup

The translator connects to a local Ollama server at `http://127.0.0.1:11434`.
Install Ollama, pull a model, and make sure the server is running before starting
the translator.

### Windows

Download and run the installer from [ollama.com/download](https://ollama.com/download).
Open PowerShell after installation:

```powershell
ollama --version
ollama pull qwen2.5:7b
ollama list
uv run deadlock-translate .\data\transcriptions --language ru
```

The Ollama application starts its server in the background. If the translator
cannot connect to `127.0.0.1:11434`, open the Ollama application from the Start
menu and run the command again.

### macOS

Download and install Ollama from [ollama.com/download](https://ollama.com/download).
After opening the application once, run the following in Terminal:

```bash
ollama --version
ollama pull qwen2.5:7b
ollama list
uv run deadlock-translate ./data/transcriptions --language ru
```

The application keeps the Ollama server running in the background. Open it again
if the translator cannot connect.

### Linux

Install Ollama and start its server:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

Leave `ollama serve` running in the first terminal. In another terminal, pull the
model and start translation:

```bash
ollama pull qwen2.5:7b
ollama list
uv run deadlock-translate ./data/transcriptions --language ru
```

If Ollama is installed as a systemd service, use this instead of `ollama serve`:

```bash
sudo systemctl start ollama
sudo systemctl status ollama
```

## Extract game assets

Use [Source 2 Viewer](https://github.com/ValveResourceFormat/ValveResourceFormat)
to browse Deadlock VPK archives and extract the audio and subtitle files into one
directory before running this tool.

## Run

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions
```

The input directory is scanned recursively. Supported audio formats are WAV, MP3,
OGG, FLAC, M4A, AAC, and Opus. Supported subtitle formats are JSON, SRT, and VTT.
The console displays completed files, percentage, an ETA, and the current hero as
its position among all heroes. When Whisper processes a file, it prints the
input-relative path and final recognized text. The tool saves each hero's JSON
file before moving to the next hero, then releases that hero's entries from
memory. When processing finishes, it also reports how many lines came from the
catalogue, subtitles, Whisper, and the previous output.

Use GPU settings when the local Whisper installation supports CUDA:

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --model large-v3 --device cuda --compute-type float16
```

Use `--overwrite` to ignore entries already present in the output directory:

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions --overwrite
```

## Whisper prompts

For audio that still needs Whisper, the tool supplies a short prompt for the
hero being processed. This helps preserve Deadlock names such as `Grey Talon`
instead of phonetically similar alternatives. The default file is
`data/hero-prompts.json`; it maps an asset code to the spellings Whisper should
recognize:

```json
{
  "heroes": {
    "orion": ["Grey Talon", "Orion"]
  }
}
```

Pass another file with `--hero-prompts-file`, or prepend shared context to every
hero prompt with `--initial-prompt`. Whisper uses `condition_on_previous_text=False`
because game voice lines are short, independent recordings.

## Hero names

The tool derives a hero name from the path segment following `hero`, `heroes`,
`character`, `characters`, `npc`, `vo`, or `voice`. For example,
`sounds/vo/chessmaster/emote/line.mp3` belongs to `chessmaster`. If none is
present, it uses the audio file's parent directory. For another layout, pass a
regular expression with a named `hero` group:

```bash
uv run deadlock-transcribe ./data/assets ./data/transcriptions \
  --hero-regex '.*/vo/(?P<hero>[^/]+)/.*'
```

## Subtitle matching

JSON subtitle files can use any of these forms:

```json
{
  "heroes/kelvin/kill_01.wav": "Target eliminated."
}
```

```json
{
  "entries": [
    {
      "audio": "heroes/kelvin/kill_01.wav",
      "text": {"en": "Target eliminated."}
    }
  ]
}
```

The tool also accepts `subtitles` or `lines` instead of `entries`; each item may
use `id`, `path`, `file`, or `audio` for its audio identifier. An SRT or VTT file
matches audio with the same relative path and filename without its extension.

## Existing transcripts

Use [Deadlock-Transcriptions](https://github.com/mcallbosco/Deadlock-Transcriptions)
before running Whisper. Its schema-v3 files store text by audio SHA-256:

```bash
git clone https://github.com/mcallbosco/Deadlock-Transcriptions.git \
  ./data/deadlock-transcriptions

uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --transcripts-dir ./data/deadlock-transcriptions/transcripts
```

Before processing each hero, the tool reads only that hero's directory in the
catalogue. It first matches the input-relative audio path to the schema-v3
`filename` (with `sounds/vo/` removed), then verifies the SHA-256 within that
record's revisions. A match is written with
`source: "mcallbosco-deadlock-transciptions"`, so Whisper is not started for the
line. `meta` retains the source `filename`, `source`, optional `model`, and
`schema_version` from the schema-v3 revision. You can pass `--transcripts-dir`
more than once.

## Output

The command writes one JSON file per hero to the output directory, for example
`transcriptions/Kelvin.json`. Each file is a JSON array. `id` is the input-relative
POSIX path, `hash` is the SHA-256 hash of the audio content, and `duration` is in
seconds. Each language keeps its own text, source, and metadata.

```json
[
  {
    "id": "heroes/Kelvin/kill_01.wav",
    "hash": "f34f30f7a69e8f0a6df42ce4d2c9f7b9cb1e93b415970c0c05e4d4ca6e3668c7",
    "text": {
      "en": {
        "text": "Target eliminated.",
        "source": "subtitle",
        "meta": {}
      }
    },
    "duration": 1.42
  }
]
```

`text.en.source` is `mcallbosco-deadlock-transciptions` for an external transcript
match, `subtitle` for text found in a subtitle file, and `whisper` for a local
transcription. On later runs, an entry with the same audio hash is reused, so the
tool does not transcribe that audio again. Add `text.ru` with its own `text`,
`source`, and `meta` when a Russian translation is available. Whisper entries add
the exact `--model` value as `text.en.meta.model`.

## Translation

`deadlock-translate` adds text in any requested language to the existing hero JSON
files through a local Ollama model. Pull Qwen first, then run the translator against the output
directory:

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions
```

The default target is Russian (`text.ru`). Select another ISO language code with
`--language`; for example, this writes German into `text.de`:

```bash
uv run deadlock-translate ./data/transcriptions --language de
```

To split work between machines, pass `--hero` once for each hero JSON filename.
Names are case-insensitive and a missing file is reported as an error:

```bash
uv run deadlock-translate ./data/transcriptions \
  --language ru \
  --hero orion \
  --hero haze \
  --hero inferno
```

It leaves non-empty text in the selected language unchanged, so it is safe to
resume or run again. Use `--overwrite` to replace it, `--model` to select another
pulled Qwen model, and `--endpoint` to use a non-default Ollama URL. New
translations use `source: "qwen-ollama"` and record the selected model in their
`meta.model`.

The console displays a progress bar with ETA, the current voice-line ID, the
English source, and the resulting translation.

For `--language ru`, the translator automatically checks
`data/citadel_generated_vo_russian.txt` first. It matches the official Valve
subtitle token to the audio filename and writes the ready-made translation with
`source: "original"`; only unmatched lines are sent to Qwen. Pass another
official localization file with `--game-localization-file` when translating a
different language.

For Russian, the default `data/translation-glossary.ru.json` supplies locked
Deadlock names and corrections for common model mistakes. A glossary contains
prompt terms plus deterministic replacements applied after the model response:

```json
{
  "terms": {"Grey Talon": "Серый Коготь"},
  "replacements": {"Серый Талон": "Серый Коготь"}
}
```

The translator includes the terms and voice-line ID in the Ollama prompt, requests
a JSON response, and then applies the replacements. Use `--glossary-file` to
select a different glossary; missing default files for other languages are ignored.
