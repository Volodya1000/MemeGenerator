"""Check real Commons image discovery and downloaded image integrity."""

import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.commons.provider import (
    CommonsImageProvider,
)

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Require one genuinely downloaded, decodable Commons photograph."""
    scene: Scene = Scene(
        order=1,
        description='Когда машина сломалась',
        image_query='broken car',
        meme_id='reaction',
    )
    with TemporaryDirectory() as directory:
        asset: ImageAsset = CommonsImageProvider().fetch(
            scene,
            Path(directory),
        )
        with Image.open(asset.image_path) as photo:
            photo.verify()
        LOGGER.info('REAL_COMMONS_PHOTO_OK: %s', asset.source_url)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
