"""Credentials and bounded search preferences for optional Pexels photos."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class PexelsSettings(BaseModel):
    """Keep the API key masked and validate the search filters."""

    model_config = ConfigDict(extra='forbid')

    api_key: SecretStr | None = None
    orientation: Literal['landscape', 'portrait', 'square'] = 'landscape'
    size: Literal['large', 'medium', 'small'] = 'large'
    per_page: int = Field(default=15, ge=1, le=80)
    timeout_seconds: float = Field(default=15, gt=0, le=60)
