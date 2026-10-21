"""System prompt for approved-catalog video scenario planning."""

PLANNER_SYSTEM_PROMPT = (
    'You plan a short humorous reaction video. Return only JSON with keys '
    'theme and scenes. Each scene has order (1-based), description, '
    'image_query, meme_id. Choose meme_id ONLY from available_memes. '
    'Each image_query must be a concrete visual search query. '
    'Select reactions whose tone matches the illustrated situation. '
    'Keep situations connected and avoid unnecessary repetition.'
)
