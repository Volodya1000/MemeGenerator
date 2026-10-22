"""Fixed FFmpeg video output and image-card encoding parameters."""

FRAMES_PER_SECOND = 30
SAMPLE_RATE = 48000
IMAGE_DURATION_SECONDS = 5
VIDEO_FILTER = (
    'scale=1280:720:force_original_aspect_ratio=decrease,'
    'pad=1280:720:(ow-iw)/2:(oh-ih)/2,'
    'setsar=1,fps=30,format=yuv420p'
)
