"""One ordered situation and the reaction chosen for it."""

from pydantic import BaseModel, Field


class Scene(BaseModel):
    """A context image query followed by a known reaction clip."""

    order: int = Field(ge=1)
    description: str = Field(min_length=1)
    image_query: str = Field(min_length=1)
    meme_id: str = Field(min_length=1)
