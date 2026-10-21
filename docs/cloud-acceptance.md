# Remote acceptance without a local development environment

On GitHub, open **Actions > Remote acceptance and downloadable synthetic demo**
and choose **Run workflow**. The workflow needs no API keys or local tools.

The first job runs `uv run meme-assets --download --force` against the seven
pinned original source files and executes real-media importer and generator
verification. No downloaded third-party MP4 or derivative is uploaded or
committed; the GitHub runner discards them after the run.

The second job uses original generated typography to illustrate three
recognizable developer situations and three clearly labelled reaction
placeholders. It intentionally includes **no synthetic impersonation or
monotonous sine-wave sound**. The real importer and video-rendering pipeline
assemble a meaningful, ordered story.
The `meme-generator-synthetic-preview` artifact contains a playable MP4,
a poster PNG, and both scenario and attribution manifests. Download that artifact from the
completed workflow page. GitHub retains it for three days.

The synthetic video proves media assembly and publication, **not** the
appearance or wording of the real Tinkov clips. Publishing downloaded real
media requires checking the applicable rights and permission separately.

Run the strict standard CI checks on the pull request before merging. The
remote acceptance jobs are additional integration checks, not substitutes
for the offline tests.

To render situational captions locally without Commons, set `images: cards`
in `config.yaml`. Each scene's `image_query` becomes the visible caption.
The real-media acceptance job separately checks a complete three-reaction
video from the pinned clips, but never uploads that copyrighted output.
