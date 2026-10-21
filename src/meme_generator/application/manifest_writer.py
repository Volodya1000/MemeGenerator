"""Persist typed generation manifests using Pydantic serialization."""

from pathlib import Path

from pydantic import BaseModel

from meme_generator.domain.attribution import (
    AttributionManifest,
    SceneAttribution,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scenario import Scenario


def write_json(path: Path, payload: BaseModel) -> None:
    """Write a validated Pydantic model as Unicode JSON."""
    path.write_text(
        payload.model_dump_json(indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def write_manifests(
    output_path: Path,
    scenario: Scenario,
    images: list[ImageAsset],
) -> None:
    """Publish the validated scenario and typed provenance records."""
    provenance = AttributionManifest(
        root=[
            SceneAttribution(
                scene_order=scene.order,
                query=scene.image_query,
                source_url=image.source_url,
                license=image.license_name,
            )
            for scene, image in zip(scenario.scenes, images, strict=True)
        ],
    )
    write_json(output_path.with_suffix('.scenario.json'), scenario)
    write_json(output_path.with_suffix('.attribution.json'), provenance)
