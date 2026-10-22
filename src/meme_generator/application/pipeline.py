"""Coordinate generation and publish a recoverable output bundle."""

from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.application.manifest_writer import write_manifests
from meme_generator.application.output_publisher import publish_bundle
from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.application.protocols.meme_repository import (
    MemeRepositoryProtocol,
)
from meme_generator.application.protocols.scenario_planner import (
    ScenarioPlannerProtocol,
)
from meme_generator.application.protocols.video_renderer import (
    VideoRendererProtocol,
)
from meme_generator.domain.generated_video import GeneratedVideo
from meme_generator.domain.scenario import Scenario


class GenerationPipeline:
    """Orchestrate typed domain planning, media, and safe publication."""

    def __init__(
        self,
        catalog: MemeRepositoryProtocol,
        planner: ScenarioPlannerProtocol,
        image_provider: ImageProviderProtocol,
        renderer: VideoRendererProtocol,
    ) -> None:
        """Inject application-level dependencies without global state."""
        self._catalog = catalog
        self._planner = planner
        self._images = image_provider
        self._renderer = renderer

    def generate(
        self,
        theme: str,
        scene_count: int,
        output_path: Path,
    ) -> GeneratedVideo:
        """Publish an MP4 only after all accompanying metadata is ready."""
        if not theme.strip():
            raise ValueError('Theme cannot be empty')
        if scene_count < 1:
            raise ValueError('At least one scene is required')
        scenario = self._planner.plan(
            theme,
            self._catalog.all(),
            scene_count,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(
            prefix='memegen-stage-',
            dir=output_path.parent,
        ) as temporary:
            self._render_and_publish(scenario, output_path, Path(temporary))
        return GeneratedVideo(
            output_path=output_path,
            scene_count=len(scenario.scenes),
            theme=scenario.theme,
        )

    def _render_and_publish(
        self,
        scenario: Scenario,
        output_path: Path,
        directory: Path,
    ) -> None:
        """Stage images, MP4 and manifests before touching final artifacts."""
        images_directory = directory / 'images'
        images_directory.mkdir()
        images = [
            self._images.fetch(
                scene, images_directory
            )
            for scene in scenario.scenes
        ]
        staged_video = directory / output_path.name
        self._renderer.render(scenario, self._catalog, images, staged_video)
        write_manifests(staged_video, scenario, images)
        publish_bundle(staged_video, output_path)
