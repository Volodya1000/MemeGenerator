"""User-facing visual composition modes for each situation."""

from enum import StrEnum


class SlideMode(StrEnum):
    """Choose the appearance of a situation before its reaction clip."""

    TEXT_ONLY = 'text_only'
    IMAGE_ONLY = 'image_only'
    IMAGE_WITH_CAPTION = 'image_with_caption'
