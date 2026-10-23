# Unsplash photo search in MemeGenerator

`images: photos` uses **Unsplash → Pexels (if configured) → Wikimedia Commons → text card**.
Unsplash requires only an **Access Key**. Do not use Project ID or Secret Key
for public searches. Never put either secret in git, YAML or an issue.

## GitHub Actions setup

1. From your [Unsplash applications](https://unsplash.com/oauth/applications),
   copy the application **Access Key** (not Secret Key).
2. In the GitHub repository: **Settings → Secrets and variables → Actions →
   New repository secret**. Name it `MEMEGEN_UNSPLASH__ACCESS_KEY`.
   Paste only the Access Key as its value.
3. Make sure the existing `MEMEGEN_LLM__API_KEY` secret for Gemini is also
   configured.
4. Run **Actions → Generate real meme video with Gemini → Run workflow**.
   Select branch, enter a topic, choose `images: photos` and
   `slide_mode: image_with_caption`, and start the workflow.
5. Download the `meme-generator-gemini-real-review` Actions artifact.
   It includes the real MP4, scenario and per-image attribution JSON.
6. For strict media acceptance, run
   **Validate real Unsplash photos in a Gemini meme video**. The job checks
   source reaction clips, photographed frames and photo provenance, and
   uploads `meme-generator-photo-search-review` as an artifact.

The strict photo acceptance workflow fails quickly without the key.
Regular video generation retains a Commons/card fallback when a photo
provider fails. A card-only scene causes the photographic verification
step to fail in `gemini-generate.yml` when `images: photos` is selected.

## Local use

Use a gitignored `.env` file:

```dotenv
MEMEGEN_UNSPLASH__ACCESS_KEY=your-unsplash-access-key
```

Non-secret parameters can be placed in `config.yaml`:

```yaml
images: photos
slide_mode: image_with_caption
unsplash:
  orientation: landscape
  per_page: 15
  timeout_seconds: 15
```

Requests use `Authorization: Client-ID <Access Key>` on
`https://api.unsplash.com`; credentials are **never** sent to
`images.unsplash.com`. The adapter downloads a returned CDN image URL
and calls the provided authenticated `download_location` exactly once
after successfully choosing and verifying the image. The attribution
manifest records the photo page, Unsplash license, photographer and
profile with referral markers.

Demo apps are limited to 50 API requests per hour (including tracking
calls); production requires approval. Review the
[API documentation](https://unsplash.com/documentation) and
[API guidelines](https://help.unsplash.com/en/articles/2511245-unsplash-api-guidelines).
The API mandates hotlinking in displayed integrations; because an exported
offline MP4 embeds photos rather than using web image URLs, confirm with
Unsplash that this rendering workflow is acceptable for your deployment.
Licenses, person rights and rights to the original reaction footage still
require review.
