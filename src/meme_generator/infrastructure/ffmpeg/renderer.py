"""Assemble a complete MP4 from ordered contextual image/reaction pairs."""

from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.application.protocols.video_renderer import (
    VideoRendererProtocol,
)
from meme_generator.application.protocols.meme_repository import (
    MemeRepositoryProtocol,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.ffmpeg.command import execute_ffmpeg
from meme_generator.infrastructure.ffmpeg.segments import (
    render_clip,
    render_image,
)


def prepare_pair(
    scene: Scene,
    image: ImageAsset,
    catalog: MemeRepositoryProtocol,
    directory: Path,
) -> tuple[Path, Path]:
    """Encode one ordered image and reaction pair."""
    context_path = directory / f'{scene.order}-context.mp4'
    reaction_path = directory / f'{scene.order}-reaction.mp4'
    render_image(image.image_path, context_path)
    render_clip(catalog.get(scene.meme_id).video_path, reaction_path)
    return context_path, reaction_path


def create_playlist(
    scenario: Scenario,
    catalog: MemeRepositoryProtocol,
    images: list[ImageAsset],
    directory: Path,
) -> Path:
    """Prepare all paired segments and a safe relative concat playlist."""
    segments = [
        clip
        for scene, image in zip(scenario.scenes, images, strict=True)
        for clip in prepare_pair(scene, image, catalog, directory)
    ]
    playlist = directory / 'concat.txt'
    playlist.write_text(
        ''.join(f"file '{part.name}'\n" for part in segments),
        encoding='utf-8',
    )
    return playlist


class FFmpegRenderer(VideoRendererProtocol):
    """Produce an MP4 atomically, preserving pre-existing output on error."""

    def render(
        self,
        scenario: Scenario,
        catalog: MemeRepositoryProtocol,
        images: list[ImageAsset],
        output_path: Path,
    ) -> Path:
        """Concatenate normalized streams and publish on success only."""
        if len(images) != len(scenario.scenes):
            raise ValueError('Scene and image counts must agree')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(
            prefix='memegen-',
            dir=output_path.parent,
        ) as temporary:
            directory = Path(temporary)
            playlist = create_playlist(scenario, catalog, images, directory)
            rendered = directory / 'complete.mp4'
            execute_ffmpeg(
                [
                    '-f',
                    'concat',
                    '-safe',
                    '0',
                    '-i',
                    str(playlist),
                    '-c',
                    'copy',
                    '-movflags',
                    '+faststart',
                    str(rendered),
                ]
            )
            rendered.replace(output_path)
        return output_path
