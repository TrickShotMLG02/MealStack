from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


METADATA_KEYS = {
    "exif",
    "icc_profile",
    "xmp",
    "XML:com.adobe.xmp",
    "photoshop",
}


@dataclass(frozen=True)
class ImageMetadataStripResult:
    content: ContentFile
    had_metadata: bool
    format: str


def _save_format(filename: str, image_format: str | None) -> str:
    if image_format:
        return image_format

    extension = Path(filename).suffix.lower()
    if extension in {".jpg", ".jpeg"}:
        return "JPEG"
    if extension == ".png":
        return "PNG"
    if extension == ".webp":
        return "WEBP"
    if extension == ".gif":
        return "GIF"
    return "PNG"


def image_has_metadata(image: Image.Image) -> bool:
    if image.getexif():
        return True

    return any(key in image.info for key in METADATA_KEYS)


def strip_image_metadata(file_obj, filename: str) -> ImageMetadataStripResult:
    position = file_obj.tell() if hasattr(file_obj, "tell") else None
    try:
        file_obj.seek(0)
    except (AttributeError, OSError):
        pass

    try:
        with Image.open(file_obj) as image:
            had_metadata = image_has_metadata(image)
            image_format = _save_format(filename, image.format)
            stripped = ImageOps.exif_transpose(image)

            if image_format == "JPEG" and stripped.mode not in {"RGB", "L"}:
                stripped = stripped.convert("RGB")

            output = BytesIO()
            save_kwargs = {}
            if image_format == "JPEG":
                save_kwargs.update({"quality": 95, "optimize": True})
            elif image_format == "PNG":
                save_kwargs.update({"optimize": True})

            stripped.save(output, format=image_format, **save_kwargs)
            output.seek(0)
            return ImageMetadataStripResult(
                content=ContentFile(output.read(), name=Path(filename).name),
                had_metadata=had_metadata,
                format=image_format,
            )
    except UnidentifiedImageError:
        raise
    finally:
        if position is not None:
            try:
                file_obj.seek(position)
            except (AttributeError, OSError):
                pass
