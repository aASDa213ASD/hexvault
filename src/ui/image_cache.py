from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image as PILImageModule

from src.database.connection import VAR_DIR

CACHE_DIR = VAR_DIR / "cache" / "images"


def _cache_key(image_url: str, resize: tuple[int, int] | None) -> str:
    size_part = "original" if resize is None else f"{resize[0]}x{resize[1]}"
    digest = hashlib.sha256(f"{image_url}|{size_part}".encode("utf-8")).hexdigest()
    return digest


def get_cached_image_path(image_url: str, resize: tuple[int, int] | None = None) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{_cache_key(image_url, resize)}.png"


def ensure_cached_image(
    image_url: str | None,
    resize: tuple[int, int] | None = None,
) -> Path | None:
    if not image_url:
        return None

    cache_path = get_cached_image_path(image_url, resize)
    if cache_path.exists():
        return cache_path

    request = Request(
        image_url,
        headers={"User-Agent": "Hexvault/1.0"},
    )
    with urlopen(request, timeout=10) as response:
        image_bytes = response.read()

    with PILImageModule.open(BytesIO(image_bytes)) as image:
        rendered = image.convert("RGBA")
        if resize is not None:
            rendered = rendered.resize(resize)
        rendered.save(cache_path, format="PNG")

    return cache_path


def prewarm_images(
    image_urls: list[str],
    resize: tuple[int, int] | None = None,
) -> None:
    for image_url in image_urls:
        try:
            ensure_cached_image(image_url, resize)
        except Exception:
            continue
