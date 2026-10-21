"""Typed payload passed to the model as its planning context."""

from pydantic import BaseModel, Field


class AvailableMeme(BaseModel):
    """One permitted reaction available to the scene planner."""

    meme_id: str
    phrase: str


class PlannerRequest(BaseModel):
    """Validate LLM context before serializing a JSON request."""

    topic: str = Field(min_length=1)
    scene_count: int = Field(ge=1)
    available_memes: list[AvailableMeme] = Field(min_length=1)
