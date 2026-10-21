"""Connect scenario planning, image acquisition, and video assembly."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.application.planning import ScenarioPlanner
from meme_generator.domain.models import GeneratedVideo, Scenario
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.images import ImageAsset, ImageProvider
from meme_generator.infrastructure.rendering import FFmpegRenderer


def write_json(path: Path, payload: object) -> None:
    """Serialize a reusable machine-readable manifest in UTF-8."""
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def write_manifests(
    output_path: Path,
    scenario: Scenario,
    images: list[ImageAsset],
) -> None:
    """Persist the validated plan and the image license provenance."""
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
    """Orchestrate adapters with no hidden mutable global state."""

    def __init__(
        self,
        catalog: MemeCatalog,
        planner: ScenarioPlanner,
        image_provider: ImageProvider,
        renderer: FFmpegRenderer,
    ) -> None:
        """Store the external dependencies of a generation request."""
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
        """Produce a video and source manifests for one requested topic."""
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
