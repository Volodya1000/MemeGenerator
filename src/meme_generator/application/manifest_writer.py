"""Serialize typed Pydantic generation manifests as JSON."""

from pathlib import Path

from pydantic import BaseModel

from meme_generator.application.output_artifacts import OutputArtifacts
from meme_generator.domain.attribution import (
    AttributionManifest,
    SceneAttribution,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scenario import Scenario


def write_json(path: Path, payload: BaseModel) -> None:
    """Persist a validated Unicode-capable model to its staged path."""
    path.write_text(
        payload.model_dump_json(indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def write_manifests(
    output_path: Path,
    scenario: Scenario,
    images: list[ImageAsset],
) -> None:
    """Serialize scenario and image provenance in the staging workspace."""
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
    paths = OutputArtifacts.from_video(output_path)
    write_json(paths.scenario, scenario)
    write_json(paths.attribution, provenance)
