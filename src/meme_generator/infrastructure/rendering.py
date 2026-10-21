"""Normalize and concatenate image cards and recorded reaction clips."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.domain.models import Scenario, Scene
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.images import ImageAsset
from meme_generator.infrastructure.media_probe import probe_clip

FPS = 30
SAMPLE_RATE = 48000
IMAGE_SECONDS = 2
INPUT_FLAG = '-i'
MAP_FLAG = '-map'
VIDEO_FILTER = (
    'scale=1280:720:force_original_aspect_ratio=decrease,'
    'pad=1280:720:(ow-iw)/2:(oh-ih)/2,'
    'setsar=1,fps=30,format=yuv420p'
)


def execute_ffmpeg(arguments: list[str]) -> None:
    """Use subprocess argument arrays rather than shell interpolation."""
    subprocess.run(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def render_image(source: Path, target: Path) -> None:
    """Encode a static image as a short H.264/AAC video segment."""
    execute_ffmpeg(
        [
            '-loop',
            '1',
            '-framerate',
            str(FPS),
            INPUT_FLAG,
            str(source),
            '-f',
            'lavfi',
            INPUT_FLAG,
            f'anullsrc=channel_layout=stereo:sample_rate={SAMPLE_RATE}',
            '-t',
            str(IMAGE_SECONDS),
            '-vf',
            VIDEO_FILTER,
            MAP_FLAG,
            '0:v:0',
            MAP_FLAG,
            '1:a:0',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-ar',
            str(SAMPLE_RATE),
            '-ac',
            '2',
            '-shortest',
            str(target),
        ]
    )


def render_clip(source: Path, target: Path) -> None:
    """Normalize a reaction's video/audio and add silence if necessary."""
    metadata = probe_clip(source)
    arguments = [INPUT_FLAG, str(source)]
    if not metadata.has_audio:
        arguments.extend(
            [
                '-f',
                'lavfi',
                INPUT_FLAG,
                f'anullsrc=channel_layout=stereo:sample_rate={SAMPLE_RATE}',
            ]
        )
    audio_input = '0:a:0' if metadata.has_audio else '1:a:0'
    execute_ffmpeg(
        [
            *arguments,
            MAP_FLAG,
            '0:v:0',
            MAP_FLAG,
            audio_input,
            '-vf',
            VIDEO_FILTER,
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-ar',
            str(SAMPLE_RATE),
            '-ac',
            '2',
            '-shortest',
            str(target),
        ]
    )


def prepare_pair(
    scene: Scene,
    image: ImageAsset,
    catalog: MemeCatalog,
    directory: Path,
) -> tuple[Path, Path]:
    """Produce context then reaction segments for exactly one scene."""
    context_path = directory / f'{scene.order}-context.mp4'
    reaction_path = directory / f'{scene.order}-reaction.mp4'
    render_image(image.image_path, context_path)
    render_clip(catalog.get(scene.meme_id).video_path, reaction_path)
    return context_path, reaction_path


class FFmpegRenderer:
    """FFmpeg montage implementation behind one application entrypoint."""

    def render(
        self,
        scenario: Scenario,
        catalog: MemeCatalog,
        images: list[ImageAsset],
        output_path: Path,
    ) -> Path:
        """Preserve scene ordering and use compatible H.264/AAC streams."""
        if len(images) != len(scenario.scenes):
            raise ValueError('Scene and image counts must agree')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='memegen-') as directory:
            segments = [
                clip
                for scene, image in zip(scenario.scenes, images, strict=True)
                for clip in prepare_pair(
                    scene, image, catalog, Path(directory)
                )
            ]
            playlist = Path(directory) / 'concat.txt'
            playlist.write_text(
                ''.join(f"file '{part}'\n" for part in segments),
                encoding='utf-8',
            )
            execute_ffmpeg(
                [
                    '-f',
                    'concat',
                    '-safe',
                    '0',
                    INPUT_FLAG,
                    str(playlist),
                    '-c',
                    'copy',
                    '-movflags',
                    '+faststart',
                    str(output_path),
                ]
            )
        return output_path
