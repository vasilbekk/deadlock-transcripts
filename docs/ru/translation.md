# Перевод

[English version](../translation.md)

`deadlock-translate` добавляет выбранный язык в существующие JSON-файлы героев с
помощью локальной модели Ollama.

## Запуск

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions --language ru
```

По умолчанию целевой язык русский, он записывается в `text.ru`. Для другого языка
укажите ISO-код:

```bash
uv run deadlock-translate ./data/transcriptions --language de
```

## Аргументы командной строки

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

`INPUT_DIR` обязателен и должен содержать JSON-файлы героев. Остальные аргументы
необязательные:

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

## Продолжение и распределение работы

Непустой текст на выбранном языке остаётся без изменений, поэтому запуск можно
безопасно продолжать или повторять. Для замены используйте `--overwrite`. Чтобы
разделить работу между компьютерами, повторяйте `--hero` для каждого JSON-файла:

```bash
uv run deadlock-translate ./data/transcriptions \
  --language ru \
  --hero orion \
  --hero haze \
  --hero inferno
```

Консоль выводит progress bar с ETA, ID текущей реплики, исходный английский текст
и итоговый перевод.

## Официальные локализации и глоссарий

Для `--language ru` переводчик проверяет
`data/citadel_generated_vo_russian.txt` до Ollama. Он сопоставляет официальный
токен субтитров Valve с именем аудиофайла и записывает готовый перевод с
`source: "original"`. В Qwen попадают только несовпавшие реплики.

`data/translation-glossary.ru.json` по умолчанию закрепляет имена Deadlock и
исправляет типичные ошибки модели:

```json
{
  "terms": {"Grey Talon": "Серый Коготь"},
  "replacements": {"Серый Талон": "Серый Коготь"}
}
```

Новые переводы модели получают `source: "qwen-ollama"`, а выбранная модель
записывается в `meta.model`.
