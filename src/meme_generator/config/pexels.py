"""Credentials and bounded search preferences for optional Pexels photos."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

DEFAULT_SEARCH_LIMIT = 15
MAX_SEARCH_LIMIT = 80
DEFAULT_TIMEOUT_SECONDS = 15


class PexelsSettings(BaseModel):
    """Keep the API key masked and validate the search filters."""

    model_config = ConfigDict(extra='forbid')

    api_key: SecretStr | None = None
    orientation: Literal['landscape', 'portrait', 'square'] = 'landscape'
    size: Literal['large', 'medium', 'small'] = 'small'
    per_page: int = Field(
        default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT
    )
    timeout_seconds: float = Field(
        default=DEFAULT_TIMEOUT_SECONDS, gt=0, le=60
    )
