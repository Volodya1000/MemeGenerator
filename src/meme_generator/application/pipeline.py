"""Use-case orchestration; adapter details remain outside this module."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.application.ports.image_provider import ImageProvider
from meme_generator.application.ports.meme_repository import MemeRepository
from meme_generator.application.ports.scenario_planner import ScenarioPlanner
from meme_generator.application.ports.video_renderer import VideoRenderer
from meme_generator.domain.generated_video import GeneratedVideo
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scenario import Scenario


def write_json(path: Path, payload: object) -> None:
    """Persist a machine-readable file with proper Unicode handling."""
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def write_manifests(
    output_path: Path,
    scenario: Scenario,
    images: list[ImageAsset],
) -> None:
    """Record the validated scenario and every image's provenance."""
    provenance = [
        {
            'scene_order': scene.order,
            'query': scene.image_query,
            'source_url': image.source_url,
            'license': image.license_name,
        }
        for scene, image in zip(scenario.scenes, images, strict=True)
    ]
    write_json(
        output_path.with_suffix('.scenario.json'),
        scenario.model_dump(mode='json'),
    )
    write_json(output_path.with_suffix('.attribution.json'), provenance)


class GenerationPipeline:
    """Orchestrate repository, planner, image provider, and renderer."""

    def __init__(
        self,
        catalog: MemeRepository,
        planner: ScenarioPlanner,
        image_provider: ImageProvider,
        renderer: VideoRenderer,
    ) -> None:
        """Inject contracts rather than concrete storage or media adapters."""
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
        """Generate a video and its corresponding provenance manifests."""
        if not theme.strip():
            raise ValueError('Theme cannot be empty')
        if scene_count < 1:
            raise ValueError('At least one scene is required')
        scenario = self._planner.plan(
            theme,
            self._catalog.all(),
            scene_count,
        )
        with TemporaryDirectory(prefix='memegen-images-') as directory:
            images = [
                self._images.fetch(
                    scene.image_query, scene.order, Path(directory)
                )
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
