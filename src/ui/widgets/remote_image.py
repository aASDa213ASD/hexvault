from __future__ import annotations

from pathlib import Path

from rich_pixels import Pixels
from textual.widget import Widget

from src.ui.shared.image_cache import ensure_cached_image

_PIXELS_CACHE: dict[tuple[str, tuple[int, int] | None], Pixels] = {}


class RemoteImage(Widget):
    def __init__(
        self,
        image_url: str | None = None,
        *,
        resize: tuple[int, int] | None = None,
        loading_text: str = "Loading image...",
        empty_text: str = "No image available",
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.image_url = image_url
        self.resize = resize
        self.loading_text = loading_text
        self.empty_text = empty_text
        self._loaded_cache_key: tuple[str, tuple[int, int] | None] | None = None
        self._content: Pixels | str = empty_text if not image_url else loading_text

    def render(self) -> Pixels | str:
        return self._content

    def on_mount(self) -> None:
        self.load_from_url(self.image_url)

    def load_from_url(self, image_url: str | None) -> None:
        self.image_url = image_url

        if not image_url:
            self._loaded_cache_key = None
            self._content = self.empty_text
            self.refresh()
            return

        cache_key = (image_url, self.resize)
        cached_pixels = _PIXELS_CACHE.get(cache_key)
        if cached_pixels is not None:
            self._loaded_cache_key = cache_key
            self._content = cached_pixels
            self.refresh()
            return

        self._content = self.loading_text

        try:
            cache_path = ensure_cached_image(image_url, self.resize)
            if cache_path is not None:
                self._set_from_path(cache_path, cache_key)
            else:
                self._content = self.empty_text
        except Exception as exc:  # noqa: BLE001
            self._content = f"Failed to load image: {exc}"

        self.refresh()

    def load_from_path(self, image_path: str | Path | None) -> None:
        if not image_path:
            self._loaded_cache_key = None
            self._content = self.empty_text
            self.refresh()
            return

        path = Path(image_path)
        cache_key = (str(path.resolve()), self.resize)
        cached_pixels = _PIXELS_CACHE.get(cache_key)
        if cached_pixels is not None:
            self._loaded_cache_key = cache_key
            self._content = cached_pixels
            self.refresh()
            return

        try:
            self._set_from_path(path, cache_key)
        except Exception as exc:  # noqa: BLE001
            self._content = f"Failed to load image: {exc}"

        self.refresh()

    def _set_from_path(
        self,
        image_path: str | Path,
        cache_key: tuple[str, tuple[int, int] | None],
    ) -> None:
        pixels = Pixels.from_image_path(image_path, resize=self.resize)
        _PIXELS_CACHE[cache_key] = pixels
        self._loaded_cache_key = cache_key
        self._content = pixels
