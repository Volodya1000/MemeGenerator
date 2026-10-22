# Browser-only acceptance: real curated reactions

Open **Actions > REAL meme review video (Cutzo)** in GitHub, select
**Run workflow**, and open the completed run. No local Python, FFmpeg or LLM
API key is required.

## Real video: download this one

The **Real seven-video integration check** job runs
`uv run meme-assets --download --force`, validates all seven original
SHA-256 fingerprints, then renders three distinct genuine Tinkov interview
reactions, each preceded by a legible contextual caption.

The `meme-generator-REAL-reactions-24h` artifact contains:

- `real-reactions-review.mp4`, a playable video with original reaction
  footage and original speech;
- `real-reactions-review.scenario.json`, the ordered scene plan;
- `real-reactions-review.attribution.json`, provenance metadata.

CI additionally decodes the completed movie and compares representative
reaction frames to the genuine curated source videos. A colored placeholder
or unrelated clip cannot silently pass this source-footage check.

The artifact is retained for **one day** solely for owner review. Neither
the original files nor the generated movie is committed to Git. Check the
applicable rights and permissions before publicly redistributing any
third-party interview footage.

## Synthetic diagnostic is not the movie

The separate **Synthetic encoder regression (not a user preview)** job
tests encoding and catalog integration using invented images and audio.
It does **not** upload a movie, and is not an acceptance result for the
actual meme content.

Set `images: cards` in `config.yaml` to use readable contextual
caption cards in ordinary generation without a Commons API or local assets.

A successful real-video job, green strict CI, and a watched output are the
criteria for technical acceptance. Artistic quality and contextual humor
still require human evaluation.
