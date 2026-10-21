"""Persist successful generation plans and image attribution."""

import json
from pathlib import Path

from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scenario import Scenario


def write_json(path: Path, payload: object) -> None:
    """Serialize Unicode-rich machine-readable generation metadata."""
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def write_manifests(
    output_path: Path,
    scenario: Scenario,
    images: list[ImageAsset],
) -> None:
    """Record the validated plan and source/license of each picture."""
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
