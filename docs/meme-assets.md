# Curated reaction assets

`assets/sources.json` is the **versioned, reviewed source catalog**. It lists
seven short Oleg Tinkov reactions from the Dud interview, with Cutzo source
pages, direct HTTPS media URLs, and pinned source SHA-256 checksums. It **does
not** include video contents or a license to redistribute the clips.

## Install and import

Requirements: Python 3.13, FFmpeg with `libx264` and `aac`, and `ffprobe`.

```bash
uv sync --extra dev
uv run meme-assets --download --manifest assets/sources.json --project-root .
```

With `--download`, missing original clips are fetched from explicit `media_url`
links in `assets/sources.json` and saved as `assets/raw/<meme_id>.mp4`.
Without that flag, the importer works offline and requires these local files.
The seven source attribution pages and their corresponding media URLs are
versioned together.

The importer validates the clip's duration (0.1–60 seconds), actual audio and
video streams, pinned source SHA-256 digests, and a 50 MiB file limit. It
converts each source to MP4/H.264/AAC, 1280×720, 30 fps, normalized audio,
and outputs `assets/memes/<meme_id>.mp4`. After *every* item succeeds, it
atomically writes `assets/catalog.json` with the existing `Meme` schema.
The generated paths are relative to the project root.

Re-running reuses existing normalized videos if the source is unchanged and
the output passes media validation. Force rebuilding with:

```bash
uv run meme-assets --force
```

## Optional automated download

The seven reviewed Cutzo entries already contain direct HTTPS `media_url`
links. To explicitly fetch any missing clips, run:

```bash
uv run meme-assets --download
```

Source page links are **not** direct media links. The command does not scrape
HTML, run JavaScript, bypass authentication, follow HTTP redirects, or scrape
YouTube. Downloads are size-limited, checked by `ffprobe`, and atomically
stored in `assets/raw/`. All seven source digests are pinned, so unexpected
upstream changes fail the import rather than silently changing meme contents.

Without `--download`, there are no network requests. New sources without a
`media_url` still require manual acquisition. Missing or corrupt inputs fail
the command; it does not produce an incomplete `catalog.json`.

## Repository and CI

Tracked: curated source manifest, import code, tests, and this document.

Ignored: `assets/raw/`, `assets/memes/`, and generated `assets/catalog.json`.
Do not commit copyrighted source videos, normalized variants, or output videos.
For future deployment, store authorized assets in a private object store and
use their SHA-256 digests to verify downloaded copies.

Unit tests are offline. Standard CI FFmpeg tests use a **synthetic** clip and
never require third-party video hosting or copyright-restricted files.
A separate `Real meme media smoke test` workflow, normally started manually,
downloads all seven source videos and runs `scripts/verify_real_media.py` on
an ephemeral GitHub runner. Media models and validation live in reusable
application modules, not inside the workflow YAML.
It prints only technical metadata and never commits or publishes MP4 files.
The initial end-to-end smoke test passed on 2026-10-21:
https://github.com/Volodya1000/MemeGenerator/actions/runs/39564344286.

**Rights:** The ability to download a clip does not grant rights to republish,
modify, or distribute it. Obtain appropriate permissions for your intended
use; keep third-party media out of the public repository and CI artifacts.
