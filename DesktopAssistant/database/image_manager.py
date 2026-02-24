"""Image storage helper."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image


class ImageManager:
    """Store and resolve screenshot images."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path.home() / "DesktopAssistant"
        self.images_dir = self.base_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, image: Image.Image, image_quality: int = 95) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}_{uuid4().hex[:4]}.png"
        file_path = self.images_dir / file_name
        image.save(file_path, format="PNG", optimize=True)
        if image_quality and image_quality < 100:
            # PNG does not use JPEG quality; keep arg to match config surface.
            pass
        return f"images/{file_name}"

    def get_absolute_path(self, relative_path: str) -> Path:
        return self.base_dir / relative_path

    def delete_image(self, relative_path: str) -> bool:
        target = self.get_absolute_path(relative_path)
        if target.exists():
            target.unlink()
            return True
        return False
