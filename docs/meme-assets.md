# Curated reaction assets

`assets/sources.json` is the **versioned, reviewed source catalog**. It lists
seven short Oleg Tinkov reactions from the Dud interview, with attribution via
Cutzo source pages. It **does not** include video contents, download URLs, or a
claim that clips are licensed for redistribution.

## Install and import

Requirements: Python 3.13, FFmpeg with `libx264` and `aac`, and `ffprobe`.

```bash
uv sync --extra dev
uv run meme-assets --manifest assets/sources.json --project-root .
```

The command expects a local source file for each listed `meme_id` at
`assets/raw/<meme_id>.mp4`. On Cutzo, use the source page's download control
for clips you are authorized to use and rename the files accordingly. The
seven source pages are available in `assets/sources.json`.

The importer validates the clip's duration (0.1–60 seconds), actual audio and
video streams, optional source SHA-256 digest, and 50 MiB file limit. It
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

When you have a **direct HTTPS media URL** that you are permitted to download,
add `media_url` to the corresponding item in `assets/sources.json` and run:

```bash
uv run meme-assets --download
```

Source page links are **not** direct media links. The command does not scrape
HTML, run JavaScript, bypass authentication, follow HTTP redirects, or scrape
YouTube. Downloads are size-limited, checked by `ffprobe`, and atomically
stored in `assets/raw/`. You can optionally set a known source `sha256` in
any entry to detect silent changes to the original file.

Without `--download`, there are no network requests. Without `media_url`,
`--download` still requires manual acquisition. Missing or corrupt input
fails the command; it does not produce an incomplete `catalog.json`.

## Repository and CI

Tracked: curated source manifest, import code, tests, and this document.

Ignored: `assets/raw/`, `assets/memes/`, and generated `assets/catalog.json`.
Do not commit copyrighted source videos, normalized variants, or output videos.
For future deployment, store authorized assets in a private object store and
use their SHA-256 digests to verify downloaded copies.

Unit tests are offline. FFmpeg integration tests use a **synthetic** clip and
never require third-party video hosting or copyright-restricted files.

**Rights:** The ability to download a clip does not grant rights to republish,
modify, or distribute it. Obtain appropriate permissions for your intended
use; keep third-party media out of the public repository and CI artifacts.
