"""Core application service layer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Union

from PIL import Image

from DesktopAssistant.config import ConfigManager
from DesktopAssistant.database.excel_manager import ExcelManager
from DesktopAssistant.database.image_manager import ImageManager
from DesktopAssistant.utils.helpers import infer_content_type, normalize_tags


class AssistantCore:
    """Coordinate config, record storage, and image storage."""

    def __init__(self, base_dir: Optional[Path] = None, config_path: Optional[Path] = None) -> None:
        def _ensure_writable(path: Path) -> bool:
            try:
                path.mkdir(parents=True, exist_ok=True)
                probe = path / ".write_probe"
                probe.write_text("ok", encoding="utf-8")
                probe.unlink(missing_ok=True)
                return True
            except OSError:
                return False

        if base_dir is not None:
            candidate = Path(base_dir)
            candidate.mkdir(parents=True, exist_ok=True)
            self.base_dir = candidate
        else:
            preferred = Path(
                os.environ.get("DESKTOP_ASSISTANT_HOME", str(Path.home() / "DesktopAssistant"))
            )
            if _ensure_writable(preferred):
                self.base_dir = preferred
            else:
                fallback = Path.cwd() / "DesktopAssistantData"
                fallback.mkdir(parents=True, exist_ok=True)
                self.base_dir = fallback

        config_file = config_path or (self.base_dir / "config.json")
        self.config = ConfigManager(config_path=str(config_file))
        self.excel_manager = ExcelManager(base_dir=self.base_dir)
        self.image_manager = ImageManager(base_dir=self.base_dir)

    def save_entry(
        self,
        *,
        text: str = "",
        tags: str = "",
        note: str = "",
        image: Optional[Image.Image] = None,
        image_path: str = "",
    ) -> dict[str, Any]:
        raw_alias_map = self.config.get("tag_alias_map", {})
        alias_map = raw_alias_map if isinstance(raw_alias_map, dict) else {}
        normalized_tags = " ".join(normalize_tags(tags, alias_map=alias_map))
        final_image_path = image_path
        if image is not None:
            final_image_path = self.image_manager.save_image(
                image, image_quality=int(self.config.get("image_quality", 95))
            )

        content_type = infer_content_type(text, final_image_path)
        record_id = self.excel_manager.add_record(
            tags=normalized_tags,
            content_type=content_type,
            text_content=text,
            image_path=final_image_path,
            note=note,
        )
        record = self.excel_manager.get_record(record_id)
        if record is None:
            raise RuntimeError("Failed to save entry to workbook.")
        return record

    def list_entries(
        self,
        *,
        search_query: str = "",
        tag: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return self.excel_manager.list_records(
            search_query=search_query,
            tag=tag,
            content_type=content_type,
            limit=limit,
            offset=offset,
        )

    def get_entry(self, record_id: int) -> Optional[dict[str, Any]]:
        return self.excel_manager.get_record(record_id)

    def update_entry(self, record_id: int, **kwargs: Any) -> bool:
        current = self.get_entry(record_id)
        if current is None:
            return False

        updates = dict(kwargs)
        old_image_path = str(current.get("image_path", ""))
        replacement_image = updates.pop("image", None)

        if "tags" in updates and updates["tags"] is not None:
            raw_alias_map = self.config.get("tag_alias_map", {})
            alias_map = raw_alias_map if isinstance(raw_alias_map, dict) else {}
            updates["tags"] = " ".join(normalize_tags(str(updates["tags"]), alias_map=alias_map))

        if replacement_image is not None:
            new_image_path = self.image_manager.save_image(
                replacement_image,
                image_quality=int(self.config.get("image_quality", 95)),
            )
            updates["image_path"] = new_image_path
            if old_image_path and old_image_path != new_image_path:
                self.image_manager.delete_image(old_image_path)
        elif "image_path" in updates:
            target_image_path = str(updates.get("image_path", ""))
            if old_image_path and target_image_path != old_image_path:
                self.image_manager.delete_image(old_image_path)

        text_content = updates.get("text_content", current.get("text_content", ""))
        image_path = updates.get("image_path", current.get("image_path", ""))
        if "content_type" not in updates:
            updates["content_type"] = infer_content_type(str(text_content), str(image_path))

        return self.excel_manager.update_record(record_id, **updates)

    def delete_entry(self, record_id: int, remove_image: bool = False) -> bool:
        record = self.excel_manager.get_record(record_id)
        if record is None:
            return False

        if remove_image and record.get("image_path"):
            self.image_manager.delete_image(record["image_path"])

        return self.excel_manager.delete_record(record_id)

    def available_tags(self) -> list[str]:
        return self.excel_manager.available_tags()

    def export_excel(
        self,
        output_path: Union[Path, str],
        *,
        search_query: str = "",
        tag: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Path:
        records = self.list_entries(
            search_query=search_query,
            tag=tag,
            content_type=content_type,
        )
        return self.excel_manager.export_to_path(Path(output_path), records=records)
