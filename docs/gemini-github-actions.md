# Generate a meme video through GitHub Actions and Google Gemini

This workflow requires no local Python, FFmpeg, or video files.

## One-time setup

1. Visit https://aistudio.google.com/api-keys and create a key in a
   **Free Tier** project. Check the model's current free-tier rate limits.
   Do not enable billing if avoiding any possible charge is important.
2. Open **Settings > Environments** and create the environment
   named exactly `MEMEGEN_LLM__API_KEY` (the current repository already has it).
3. Inside that environment choose **Add environment secret**. Name the
   secret exactly `MEMEGEN_LLM__API_KEY` and paste the Google API key.
   The workflow job selects this environment explicitly; no new repository
   secret is needed. Never paste the key into a workflow input, issue,
   PR, or config file.

## Generate

After merging this PR into `main`, open **Actions > Generate real meme video
with Gemini > Run workflow**. Fill in:

- **topic**: any description, e.g. a programmer fixing CI.
- **sizing_mode**: `scenes` for an exact number of situations and real
  reactions; `duration` for an approximate runtime.
- **scenes**: number of paired context/reaction scenes (1 to 10); only used
  in `scenes` mode.
- **target_seconds**: intended runtime (5 to 180 seconds); only used in
  `duration` mode. The app computes the approximate scene count using
  the actual average length of the downloaded reaction clips and the
  configured context-card duration.
- **context_duration_seconds**: choose how long each situation is displayed,
  with five seconds as the default; both scene-count and duration planning
  use the same setting.
- **slide_mode**: `text_only`, `image_only` or `image_with_caption`.
  In the captioned-photo mode, the Russian `description` appears on top of
  the real searched picture, while `image_query` is used only for search.
- **images**: choose `photos` (Wikimedia Commons search with a readable
  text-card fallback), `commons` (strict search), or `cards` (text-only).
  Neither mode generates AI images.

Wait for **Generate a real LLM-planned reaction video** to succeed, then
download `meme-generator-gemini-real-review` from the workflow run.
It contains the MP4, typed scene plan, and image provenance JSON.

This workflow calls the actual Gemini API: it does not use a fake,
hardcoded scenario or synthetic meme reactions. The output includes
third-party footage solely for short-lived owner review (one-day artifact);
review permissions before further redistribution.

## Troubleshooting

- **Secret missing**: check the `MEMEGEN_LLM__API_KEY` environment has
  a secret with the same name. Repository secrets and environment secrets
  are separate scopes.
- **429 quota exceeded**: inspect Google AI Studio rate limits. Free-tier
  quotas are project-level, vary by model and region, and are not guaranteed.
- **Model not found**: check current Free Tier eligibility and the model
  identifier for your account; no automatic paid-model fallback is used.
- **Photo unavailable**: `images: photos` automatically displays a text card
  with the original situation if Wikimedia returns no valid picture. Use
  `images: commons` for strict failures rather than fallback.
- **Photo licensing**: the attribution JSON stores the original source URL
  and license when a photo is downloaded.
- **Output duration**: an estimate, not a promise; original spoken
  reactions are never trimmed merely to hit a specified number of seconds.
