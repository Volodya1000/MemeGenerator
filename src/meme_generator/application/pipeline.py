"""Generate a video using typed ports and independent adapters."""

from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.application.manifest_writer import write_manifests
from meme_generator.application.ports.image_provider import ImageProvider
from meme_generator.application.ports.meme_repository import MemeRepository
from meme_generator.application.ports.scenario_planner import ScenarioPlanner
from meme_generator.application.ports.video_renderer import VideoRenderer
from meme_generator.domain.generated_video import GeneratedVideo


class GenerationPipeline:
    """Orchestrate approved reactions, planning, images, and rendering."""

    def __init__(
        self,
        catalog: MemeRepository,
        planner: ScenarioPlanner,
        image_provider: ImageProvider,
        renderer: VideoRenderer,
    ) -> None:
        """Require only application-owned ports, not concrete adapters."""
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
        """Produce a video and corresponding scenario/license manifests."""
        if not theme.strip():
            raise ValueError('Theme cannot be empty')
        if scene_count < 1:
            raise ValueError('At least one scene is required')
        scenario = self._planner.plan(
            theme,
            self._catalog.all(),
            scene_count,
        )
        with TemporaryDirectory(prefix='memegen-images-') as temporary:
            directory = Path(temporary)
            images = [
                self._images.fetch(scene.image_query, scene.order, directory)
                for scene in scenario.scenes
            ]
            self._renderer.render(
                scenario,
                self._catalog,
                images,
                output_path,
            )
            write_manifests(output_path, scenario, images)
        return GeneratedVideo(
            output_path=output_path,
            scene_count=len(scenario.scenes),
            theme=scenario.theme,
        )
