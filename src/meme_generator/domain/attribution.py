"""Typed, serializable attribution data for generated scenes."""

from pydantic import BaseModel, Field, RootModel


class SceneAttribution(BaseModel):
    """Provenance and license for one generated contextual image."""

    scene_order: int = Field(ge=1)
    query: str = Field(min_length=1)
    source_url: str
    license: str


class AttributionManifest(RootModel[list[SceneAttribution]]):
    """Ordered, validated image license records for the output video."""
