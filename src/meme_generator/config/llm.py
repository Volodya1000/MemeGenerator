"""Validated model provider and retry settings."""

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class LLMSettings(BaseModel):
    """Model provider configuration and bounded transient retries."""

    model_config = ConfigDict(extra='forbid')

    model: str = ''
    api_base: str | None = None
    api_key: SecretStr | None = None
    retry_attempts: int = Field(default=3, ge=1, le=10)
