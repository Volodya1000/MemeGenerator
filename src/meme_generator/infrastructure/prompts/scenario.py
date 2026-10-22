"""System prompt for approved-catalog video scenario planning."""

PLANNER_SYSTEM_PROMPT = (
    'You plan a short humorous reaction video. Return only JSON with keys '
    'theme and scenes. Each scene has order (1-based), description, '
    'image_query, meme_id. Choose meme_id ONLY from available_memes. '
    'Write each description in natural Russian as a short complete situation, '
    'suitable for on-screen reading. Each image_query must be a short '
    'English search query of two or three concrete keywords naming '
    'the whole subject and its surroundings in a photograph, such as '
    '"used car" or "stranded vehicle roadside". Avoid search phrases '
    'about isolated parts, close-ups or detached components. '
    'Avoid long detailed phrases. '
    'Select reactions whose tone matches the illustrated situation. '
    'Keep situations connected and avoid unnecessary repetition.'
)
