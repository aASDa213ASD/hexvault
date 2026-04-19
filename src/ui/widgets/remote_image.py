from __future__ import annotations

from io import BytesIO
from urllib.request import Request, urlopen

from PIL import Image as PILImageModule
from rich_pixels import Pixels
from textual.widget import Widget


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
        self._content: Pixels | str = empty_text if not image_url else loading_text

    def render(self) -> Pixels | str:
        return self._content

    def on_mount(self) -> None:
        self.load_from_url(self.image_url)

    def load_from_url(self, image_url: str | None) -> None:
        self.image_url = image_url

        if not image_url:
            self._content = self.empty_text
            self.refresh()
            return

        self._content = self.loading_text

        try:
            request = Request(
                image_url,
                headers={"User-Agent": "Hexvault/1.0"},
            )
            with urlopen(request, timeout=10) as response:
                image_bytes = response.read()

            with PILImageModule.open(BytesIO(image_bytes)) as image:
                self._content = Pixels.from_image(image, resize=self.resize)
        except Exception as exc:  # noqa: BLE001
            self._content = f"Failed to load image: {exc}"

        self.refresh()
