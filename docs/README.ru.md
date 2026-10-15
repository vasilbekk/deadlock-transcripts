# Deadlock Transcripts: ready-to-use tools for automatic transcription and translation

[English version](../README.md)

В этом репозитории лежат английские транскрибации всех реплик всех героев Deadlock.
Другие языки можно добавить локально, запустив `deadlock-translate` с локальной
моделью Ollama на своей видеокарте.

## Языки

- English (`en`)
- Russian (`ru`)

`deadlock-transcriber` предоставляет инструменты командной строки для сборки и
пополнения каталога. `deadlock-transcribe` обрабатывает распакованные файлы игры
локальной моделью Whisper. `deadlock-translate` добавляет переводы с помощью
локальных моделей Ollama и доступных официальных локализаций игры.

## Требования

- Python 3.11 или новее
- [uv](https://docs.astral.sh/uv/)
- FFmpeg с `ffprobe` в `PATH` для определения длительности MP3, OGG, FLAC, M4A,
  AAC и Opus. Для WAV FFmpeg не требуется.

## Установка

```bash
uv sync --extra whisper
```

Команда создаёт `.venv` и устанавливает `faster-whisper`, cuBLAS для CUDA 12 и
cuDNN 9. В Linux утилита автоматически настраивает пути к установленным CUDA
библиотекам до запуска Whisper. Модель скачается при обработке первого аудиофайла
без субтитра.

## Настройка для платформы

Переводчик работает в Windows, macOS и Linux. Для транскрибатора также нужен
FFmpeg. GPU-транскрибация в проекте настроена для Linux с NVIDIA CUDA; в Windows и
macOS используйте CPU-режим, если CTranslate2 с поддерживаемым backend не настроен
вручную.

В примере для Windows используется CPU, потому что проект автоматически настраивает
пути к пакетным CUDA-библиотекам только в Linux. Транскрибацию на NVIDIA GPU можно
запустить и в Windows после самостоятельной настройки совместимых CUDA и CTranslate2,
но это выходит за пределы настройки проекта. В Linux пример использует GPU, потому
что при доступной NVIDIA CUDA это уже настроенный и более быстрый вариант.

### Windows

Выполните команды в PowerShell из папки проекта:

```powershell
winget install --id=astral-sh.uv -e
winget install --id=Gyan.FFmpeg.Shared -e
uv python install 3.12
uv sync --extra whisper
```

Транскрибация на CPU:

```powershell
uv run deadlock-transcribe .\data\sources .\data\transcriptions --device cpu --compute-type int8
```

Установите Ollama с [ollama.com/download](https://ollama.com/download), затем
загрузите модель перевода:

```powershell
ollama pull qwen2.5:7b
uv run deadlock-translate .\data\transcriptions --language ru
```

### macOS

Сначала установите Homebrew, если его ещё нет, затем выполните:

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

Следующие команды рассчитаны на Debian и Ubuntu:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo apt update
sudo apt install ffmpeg
uv python install 3.12
uv sync --extra whisper
```

Транскрибация на NVIDIA CUDA:

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --model large-v3 --device cuda --compute-type float16
```

Для CPU замените параметры устройства в последней команде на
`--device cpu --compute-type int8`. Установите Ollama по
[инструкции для Linux](https://docs.ollama.com/linux), затем загрузите и запустите
Qwen:

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions --language ru
```

## Ollama: установка и запуск

Переводчик обращается к локальному серверу Ollama по адресу
`http://127.0.0.1:11434`. Сначала установите Ollama, затем загрузите модель и
убедитесь, что сервер запущен.

### Windows

Скачайте установщик с [ollama.com/download](https://ollama.com/download) и
запустите его. После установки откройте PowerShell:

```powershell
ollama --version
ollama pull qwen2.5:7b
ollama list
uv run deadlock-translate .\data\transcriptions --language ru
```

Приложение Ollama запускает сервер в фоне. Если команда переводчика не может
подключиться к `127.0.0.1:11434`, откройте приложение Ollama из меню Start и
повторите запуск.

### macOS

Скачайте и установите Ollama с [ollama.com/download](https://ollama.com/download).
После первого запуска приложения выполните в Terminal:

```bash
ollama --version
ollama pull qwen2.5:7b
ollama list
uv run deadlock-translate ./data/transcriptions --language ru
```

Приложение поддерживает сервер Ollama в фоне. Если переводчик не подключается,
откройте приложение Ollama ещё раз.

### Linux

Установите Ollama и запустите сервер:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

Оставьте `ollama serve` работающим в первом терминале. Во втором терминале
загрузите модель и начните перевод:

```bash
ollama pull qwen2.5:7b
ollama list
uv run deadlock-translate ./data/transcriptions --language ru
```

Если Ollama установлен как systemd-сервис, вместо `ollama serve` используйте:

```bash
sudo systemctl start ollama
sudo systemctl status ollama
```

## Извлечение файлов игры

Используйте [Source 2 Viewer](https://github.com/ValveResourceFormat/ValveResourceFormat),
чтобы открыть VPK-архивы Deadlock и извлечь аудиофайлы и субтитры в одну папку
перед запуском утилиты.

## Запуск

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions
```

Входная папка сканируется рекурсивно. Поддерживаются аудиоформаты WAV, MP3, OGG,
FLAC, M4A, AAC и Opus, а также субтитры JSON, SRT и VTT.
Консоль показывает число обработанных файлов, процент, ETA и текущего героя с его
номером среди всех героев. При обработке файла через Whisper выводятся
относительный путь и итоговый распознанный текст. После завершения каждого героя
утилита сразу сохраняет его JSON-файл и освобождает память, занятую записями этого
героя. В конце выводится число реплик из каталога, субтитров, Whisper и предыдущего
результата.

Если локальная установка Whisper поддерживает CUDA, можно использовать GPU:

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --model large-v3 --device cuda --compute-type float16
```

Чтобы не использовать записи из существующей выходной папки, укажите `--overwrite`:

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions --overwrite
```

## Аргументы командной строки

### Транскрибация

```bash
uv run deadlock-transcribe INPUT_DIR OUTPUT_DIR \
  --model large-v3 \
  --device cuda \
  --compute-type float16 \
  --hero-prompts-file ./data/hero-prompts.json \
  --initial-prompt "Реплики Deadlock" \
  --hero-regex '.*/vo/(?P<hero>[^/]+)/.*' \
  --transcripts-dir ./data/deadlock-transcriptions/transcripts \
  --transcripts-dir ./data/another-transcript-source \
  --overwrite
```

`INPUT_DIR` и `OUTPUT_DIR` — обязательные позиционные аргументы. Все остальные
аргументы необязательные:

- `--model`: имя модели faster-whisper или путь к локальной модели. По умолчанию:
  `large-v3`
- `--device`: `auto`, `cpu` или `cuda`. По умолчанию: `auto`
- `--compute-type`: тип вычислений faster-whisper, например `int8` или `float16`.
  По умолчанию: `default`
- `--hero-prompts-file`: JSON-файл с вариантами имён героев для Whisper. По
  умолчанию: `data/hero-prompts.json`
- `--initial-prompt`: текст, добавляемый к подсказке Whisper каждого героя
- `--hero-regex`: регулярное выражение с именованной группой `hero` для определения
  героя по пути к аудио
- `--transcripts-dir`: каталог транскрипций schema-v3, который проверяется до
  Whisper. Аргумент можно повторять
- `--overwrite`: не использовать записи, уже лежащие в `OUTPUT_DIR`

### Перевод

```bash
uv run deadlock-translate INPUT_DIR \
  --language ru \
  --model qwen2.5:7b \
  --endpoint http://127.0.0.1:11434 \
  --hero orion \
  --hero haze \
  --game-localization-file ./data/citadel_generated_vo_russian.txt \
  --glossary-file ./data/translation-glossary.ru.json \
  --overwrite
```

`INPUT_DIR` — обязательный аргумент: папка с JSON-файлами героев. Все остальные
аргументы необязательные:

- `--language`: целевой ISO-код языка. По умолчанию: `ru`
- `--model`: имя установленной модели Ollama. По умолчанию: `qwen2.5:7b`
- `--endpoint`: URL сервера Ollama. По умолчанию: `http://127.0.0.1:11434`
- `--hero`: имя JSON-файла героя для обработки. Повторяйте его, чтобы разделить
  работу между компьютерами. Без аргумента обрабатываются все герои
- `--game-localization-file`: официальный файл локализации, проверяемый до Ollama.
  Для русского языка по умолчанию: `data/citadel_generated_vo_russian.txt`
- `--glossary-file`: JSON-файл терминологического глоссария. По умолчанию утилита
  ищет `data/translation-glossary.<language>.json`
- `--overwrite`: заменить уже существующие переводы в `text.<language>`

## Подсказки Whisper

Для аудио, которое всё ещё требует Whisper, утилита передаёт короткую подсказку
для обрабатываемого героя. Это помогает сохранить имена Deadlock, например
`Grey Talon`, вместо фонетически похожих вариантов. По умолчанию используется
`data/hero-prompts.json`; он сопоставляет код ассета с написаниями, которые должен
распознавать Whisper:

```json
{
  "heroes": {
    "orion": ["Grey Talon", "Orion"]
  }
}
```

Другой файл можно передать через `--hero-prompts-file`, а общий контекст добавить
ко всем подсказкам с помощью `--initial-prompt`. Используется
`condition_on_previous_text=False`, поскольку игровые реплики короткие и не
зависят друг от друга.

## Имена героев

Утилита получает имя героя из сегмента пути после `hero`, `heroes`, `character`,
`characters`, `npc`, `vo` или `voice`. Например, файл
`sounds/vo/chessmaster/emote/line.mp3` относится к герою `chessmaster`. Если такого
сегмента нет, используется родительская папка аудиофайла. Для другой структуры
передайте регулярное выражение с именованной группой `hero`:

```bash
uv run deadlock-transcribe ./data/assets ./data/transcriptions \
  --hero-regex '.*/vo/(?P<hero>[^/]+)/.*'
```

## Сопоставление субтитров

JSON-файлы субтитров могут использовать любую из этих форм:

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

Также поддерживаются ключи `subtitles` и `lines` вместо `entries`. В каждой записи
для идентификатора аудио можно использовать `id`, `path`, `file` или `audio`.
Файл SRT или VTT сопоставляется с аудио, у которого совпадают относительный путь и
имя файла без расширения.

## Готовые транскрипции

Перед запуском Whisper используйте
[Deadlock-Transcriptions](https://github.com/mcallbosco/Deadlock-Transcriptions).
Его файлы формата schema-v3 хранят текст по SHA-256 хэшу аудио:

```bash
git clone https://github.com/mcallbosco/Deadlock-Transcriptions.git \
  ./data/deadlock-transcriptions

uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --transcripts-dir ./data/deadlock-transcriptions/transcripts
```

Перед обработкой каждого героя утилита читает только его папку из каталога. Сначала
она сопоставляет относительный путь аудио с `filename` schema-v3 (без префикса
`sounds/vo/`), затем проверяет SHA-256 среди ревизий этой записи. При совпадении
запись создаётся с `source: "mcallbosco-deadlock-transciptions"`, а Whisper для
этой реплики не запускается. В `meta` сохраняются `filename`, `source`,
необязательное `model` и `schema_version` из ревизии schema-v3.
`--transcripts-dir` можно передать несколько раз.

## Результат

Команда записывает один JSON-файл на героя в выходную папку, например
`transcriptions/Kelvin.json`. Каждый файл содержит JSON-массив. `id` является
относительным POSIX-путём от входной папки, `hash` содержит SHA-256 хэш аудио, а
`duration` указана в секундах. Для каждого языка отдельно хранятся текст, источник
и метаданные.

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

`text.en.source` имеет значение `mcallbosco-deadlock-transciptions` для совпадения
с внешним каталогом, `subtitle` для текста из файла субтитров и `whisper` для
локальной транскрипции. При следующих запусках запись с таким же хэшем аудио
используется повторно, поэтому аудио не транскрибируется ещё раз. Для русского
перевода можно добавить `text.ru` с собственными полями `text`, `source` и `meta`.
Для реплик Whisper в `text.en.meta.model` записывается точное значение `--model`.

## Перевод

`deadlock-translate` добавляет текст на выбранном языке в существующие JSON-файлы
героев с помощью локальной модели Ollama. Сначала загрузите Qwen, затем запустите переводчик
для папки результатов:

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions
```

По умолчанию целевой язык — русский (`text.ru`). Другой код языка ISO задаётся
через `--language`; например, эта команда запишет немецкий в `text.de`:

```bash
uv run deadlock-translate ./data/transcriptions --language de
```

Чтобы разделить работу между компьютерами, передайте `--hero` для каждого имени
JSON-файла героя. Регистр не учитывается, а отсутствующий файл приведёт к понятной
ошибке:

```bash
uv run deadlock-translate ./data/transcriptions \
  --language ru \
  --hero orion \
  --hero haze \
  --hero inferno
```

Непустой текст на выбранном языке остаётся без изменений, поэтому запуск можно
безопасно продолжать или повторять. Используйте `--overwrite` для его замены,
`--model` для выбора другой загруженной модели Qwen и `--endpoint` для нестандартного
адреса Ollama. Новые переводы получают источник `source: "qwen-ollama"`, а выбранная
модель записывается в `meta.model`.

В консоль выводятся progress bar с ETA, ID текущей реплики, исходный английский
текст и итоговый перевод.

Для `--language ru` переводчик сначала автоматически проверяет
`data/citadel_generated_vo_russian.txt`. Он сопоставляет официальный токен Valve с
именем аудиофайла и записывает готовый перевод с источником `source: "original"`;
в Qwen попадают только несовпавшие реплики. Для другого
языка путь к официальному файлу локализации передаётся через
`--game-localization-file`.

Для русского языка по умолчанию используется
`data/translation-glossary.ru.json`: в нём закреплены имена Deadlock и исправления
частых ошибок модели. Глоссарий содержит термины для prompt и детерминированные
замены, которые применяются после ответа модели:

```json
{
  "terms": {"Grey Talon": "Серый Коготь"},
  "replacements": {"Серый Талон": "Серый Коготь"}
}
```

Переводчик передаёт термины и ID реплики в prompt для Ollama, запрашивает JSON-ответ,
затем применяет замены. Другой глоссарий задаётся параметром `--glossary-file`; для
остальных языков отсутствующий файл по умолчанию просто игнорируется.
