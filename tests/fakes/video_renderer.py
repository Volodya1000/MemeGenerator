"""A typed fake renderer for application-level behavioral tests."""

from pathlib import Path

from meme_generator.application.protocols.meme_repository import (
    MemeRepositoryProtocol,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scenario import Scenario


class FakeRenderer:
    """File-producing external boundary for fast orchestration tests."""

    def render(
        self,
        scenario: Scenario,
        catalog: MemeRepositoryProtocol,
        images: list[ImageAsset],
        output_path: Path,
    ) -> Path:
        """Write a recognizable artifact without using FFmpeg."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b'video stub')
        return output_path
