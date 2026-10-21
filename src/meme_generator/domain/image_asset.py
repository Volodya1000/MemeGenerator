"""A scene image with attribution metadata."""

from pathlib import Path

from pydantic import BaseModel


class ImageAsset(BaseModel):
    """Downloaded or user-provided image available to the renderer."""

    image_path: Path
    source_url: str
    license_name: str
