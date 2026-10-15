# Транскрибация

[English version](../transcription.md)

## Извлечение файлов игры

Используйте [Source 2 Viewer](https://github.com/ValveResourceFormat/ValveResourceFormat),
чтобы открыть VPK-архивы Deadlock и извлечь аудиофайлы и субтитры в одну папку.

## Запуск

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions
```

Входная папка сканируется рекурсивно. Поддерживаются WAV, MP3, OGG, FLAC, M4A, AAC,
Opus, а также субтитры JSON, SRT и VTT. В консоль выводятся число обработанных
файлов, процент, ETA и текущий герой. После каждого героя утилита сохраняет JSON и
освобождает память, занятую его записями.

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --model large-v3 --device cuda --compute-type float16
```

Чтобы не использовать записи из выходной папки, укажите `--overwrite`.

## Аргументы командной строки

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

`INPUT_DIR` и `OUTPUT_DIR` обязательны. Остальные аргументы необязательные:

- `--model`: имя модели faster-whisper или путь к локальной модели. По умолчанию:
  `large-v3`
- `--device`: `auto`, `cpu` или `cuda`. По умолчанию: `auto`
- `--compute-type`: тип вычислений faster-whisper, например `int8` или `float16`.
  По умолчанию: `default`
- `--hero-prompts-file`: JSON-файл с вариантами имён героев для Whisper. По
  умолчанию: `data/hero-prompts.json`
- `--initial-prompt`: текст, добавляемый к подсказке Whisper каждого героя
- `--hero-regex`: регулярное выражение с именованной группой `hero`
- `--transcripts-dir`: каталог транскрипций schema-v3, который проверяется до
  Whisper. Аргумент можно повторять
- `--overwrite`: не использовать записи, уже лежащие в `OUTPUT_DIR`

## Подсказки Whisper и имена героев

Для аудио без готового текста утилита передаёт Whisper короткую подсказку для героя.
`data/hero-prompts.json` сопоставляет код ассета с вариантами написания:

```json
{
  "heroes": {
    "orion": ["Grey Talon", "Orion"]
  }
}
```

Используйте `--hero-prompts-file` для другого файла и `--initial-prompt` для
общего контекста. Герой определяется по сегменту пути после `hero`, `heroes`,
`character`, `characters`, `npc`, `vo` или `voice`. Для другой структуры укажите
`--hero-regex` с именованной группой `hero`.

## Субтитры и готовые транскрипции

JSON-файл субтитров может напрямую сопоставлять идентификатор аудио с текстом:

```json
{
  "heroes/kelvin/kill_01.wav": "Target eliminated."
}
```

Также поддерживаются массивы `entries`, `subtitles` и `lines`. В записи для аудио
можно использовать `id`, `path`, `file` или `audio`. SRT и VTT сопоставляются по
относительному пути и имени аудиофайла без расширения.

Перед Whisper используйте
[Deadlock-Transcriptions](https://github.com/mcallbosco/Deadlock-Transcriptions):

```bash
git clone https://github.com/mcallbosco/Deadlock-Transcriptions.git \
  ./data/deadlock-transcriptions

uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --transcripts-dir ./data/deadlock-transcriptions/transcripts
```

Утилита сначала сопоставляет путь аудио, затем проверяет SHA-256. Совпавшие записи
получают источник `mcallbosco-deadlock-transciptions`, поэтому Whisper не запускается.

## Результат

На каждого героя создаётся JSON-массив. Запись содержит относительный `id`, хэш
аудио, `duration` и отдельные текст, источник и метаданные для каждого языка.

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

`text.en.source` имеет значение `mcallbosco-deadlock-transciptions`, `subtitle` или
`whisper`. Для Whisper в `text.en.meta.model` записывается выбранная модель.
