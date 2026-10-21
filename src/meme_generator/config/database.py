"""Validated database backend and connection settings."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, SecretStr


class DatabaseSettings(BaseModel):
    """Storage configuration, with connection credentials kept secret."""

    model_config = ConfigDict(extra='forbid')

    backend: Literal['json', 'sqlalchemy'] = 'json'
    url: SecretStr | None = None
