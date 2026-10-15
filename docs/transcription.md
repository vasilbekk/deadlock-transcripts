# Transcription

[Русская версия](./ru/transcription.md)

## Extract game assets

Use [Source 2 Viewer](https://github.com/ValveResourceFormat/ValveResourceFormat)
to browse Deadlock VPK archives and extract audio and subtitle files into one
directory.

## Run

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions
```

The input directory is scanned recursively. Supported audio formats are WAV, MP3,
OGG, FLAC, M4A, AAC, and Opus. Supported subtitle formats are JSON, SRT, and VTT.
The console shows completed files, percentage, ETA, and the current hero. The tool
writes each hero's JSON file and releases that hero's entries before proceeding.

```bash
uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --model large-v3 --device cuda --compute-type float16
```

Use `--overwrite` to ignore entries already present in the output directory.

## Command-line arguments

```bash
uv run deadlock-transcribe INPUT_DIR OUTPUT_DIR \
  --model large-v3 \
  --device cuda \
  --compute-type float16 \
  --hero-prompts-file ./data/hero-prompts.json \
  --initial-prompt "Deadlock voice lines" \
  --hero-regex '.*/vo/(?P<hero>[^/]+)/.*' \
  --transcripts-dir ./data/deadlock-transcriptions/transcripts \
  --transcripts-dir ./data/another-transcript-source \
  --overwrite
```

`INPUT_DIR` and `OUTPUT_DIR` are required positional arguments. All other arguments
are optional:

- `--model`: faster-whisper model name or a local model path. Default: `large-v3`
- `--device`: `auto`, `cpu`, or `cuda`. Default: `auto`
- `--compute-type`: faster-whisper compute type such as `int8` or `float16`.
  Default: `default`
- `--hero-prompts-file`: JSON file with hero name variants for Whisper. Default:
  `data/hero-prompts.json`
- `--initial-prompt`: text added to every hero-specific Whisper prompt
- `--hero-regex`: regular expression with a named `hero` group for deriving the
  hero from an audio path
- `--transcripts-dir`: schema-v3 transcript directory checked before Whisper. You
  can repeat this argument
- `--overwrite`: do not reuse records already present in `OUTPUT_DIR`

## Whisper prompts and hero names

For audio that needs Whisper, the tool supplies a short prompt for the current hero.
The default `data/hero-prompts.json` maps an asset code to the spellings Whisper
should recognize:

```json
{
  "heroes": {
    "orion": ["Grey Talon", "Orion"]
  }
}
```

Use `--hero-prompts-file` to choose another file and `--initial-prompt` to prepend
common context. The tool derives a hero from the path after `hero`, `heroes`,
`character`, `characters`, `npc`, `vo`, or `voice`. Use `--hero-regex` with a named
`hero` group for another layout.

## Subtitle matching and existing transcripts

JSON subtitle files may map an audio identifier directly to text:

```json
{
  "heroes/kelvin/kill_01.wav": "Target eliminated."
}
```

They can also use an `entries`, `subtitles`, or `lines` array. Each item may use
`id`, `path`, `file`, or `audio` as its audio identifier. An SRT or VTT file matches
audio with the same relative path and filename without its extension.

Use [Deadlock-Transcriptions](https://github.com/mcallbosco/Deadlock-Transcriptions)
before Whisper to reuse its schema-v3 records:

```bash
git clone https://github.com/mcallbosco/Deadlock-Transcriptions.git \
  ./data/deadlock-transcriptions

uv run deadlock-transcribe ./data/sources ./data/transcriptions \
  --transcripts-dir ./data/deadlock-transcriptions/transcripts
```

The tool first matches the input-relative audio path, then verifies the audio
SHA-256 hash. Matched records use the source
`mcallbosco-deadlock-transciptions`, so Whisper does not run for those lines.

## Output

The command writes one JSON array per hero. Each record keeps its input-relative
`id`, audio `hash`, `duration`, and language-specific text, source, and metadata.

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

`text.en.source` is `mcallbosco-deadlock-transciptions`, `subtitle`, or `whisper`.
Whisper records add the selected model as `text.en.meta.model`.
