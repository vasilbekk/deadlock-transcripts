# Translation

[Русская версия](./ru/translation.md)

`deadlock-translate` adds a requested language to the existing per-hero JSON files
through a local Ollama model.

## Run

```bash
ollama pull qwen2.5:7b
uv run deadlock-translate ./data/transcriptions --language ru
```

The default target is Russian, written under `text.ru`. Use another ISO language
code to add another language:

```bash
uv run deadlock-translate ./data/transcriptions --language de
```

## Command-line arguments

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

`INPUT_DIR` is required and must contain per-hero JSON files. All other arguments
are optional:

- `--language`: target ISO language code. Default: `ru`
- `--model`: installed Ollama model. Default: `qwen2.5:7b`
- `--endpoint`: Ollama server URL. Default: `http://127.0.0.1:11434`
- `--hero`: hero JSON filename to process. Repeat it to split work across machines.
  Without it, the command processes every hero
- `--game-localization-file`: official localization checked before Ollama. For
  Russian, the default is `data/citadel_generated_vo_russian.txt`
- `--glossary-file`: terminology glossary JSON file. By default, the tool looks for
  `data/translation-glossary.<language>.json`
- `--overwrite`: replace translations already present under `text.<language>`

## Resuming and distributing work

Non-empty text in the selected language is left unchanged, so it is safe to resume
or run the command again. Use `--overwrite` to replace it. To split work across
computers, repeat `--hero` for each JSON filename:

```bash
uv run deadlock-translate ./data/transcriptions \
  --language ru \
  --hero orion \
  --hero haze \
  --hero inferno
```

The console displays a progress bar with ETA, the current voice-line ID, the
English source, and the resulting translation.

## Official localizations and glossary

For `--language ru`, the translator checks
`data/citadel_generated_vo_russian.txt` before Ollama. It matches the official Valve
subtitle token to the audio filename and writes the ready-made translation with
`source: "original"`. Only unmatched lines are sent to Qwen.

The default `data/translation-glossary.ru.json` supplies locked Deadlock names and
corrections for common model mistakes:

```json
{
  "terms": {"Grey Talon": "Серый Коготь"},
  "replacements": {"Серый Талон": "Серый Коготь"}
}
```

New model translations use `source: "qwen-ollama"` and record the selected model
in `meta.model`.
