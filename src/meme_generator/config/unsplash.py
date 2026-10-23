"""Credentials and bounded settings for Unsplash photo search."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

DEFAULT_SEARCH_LIMIT = 15
MAX_SEARCH_LIMIT = 30
DEFAULT_TIMEOUT_SECONDS = 15


class UnsplashSettings(BaseModel):
    """Mask the API credential and validate public image search options."""

    model_config = ConfigDict(extra='forbid')

    access_key: SecretStr | None = None
    orientation: Literal['landscape', 'portrait', 'squarish'] = 'landscape'
    per_page: int = Field(
        default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT
    )
    timeout_seconds: float = Field(
        default=DEFAULT_TIMEOUT_SECONDS, gt=0, le=60
    )
