from __future__ import annotations

import hashlib
import io
import secrets
from dataclasses import dataclass
from typing import Any

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError
from starlette.datastructures import UploadFile

from app.config import settings
from app.errors import ImageValidationError

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}


@dataclass(frozen=True)
class ImageStats:
    width: int
    height: int
    brightness: float
    contrast: float
    edge_density: float
    dominant_hex: str
    aspect_ratio: float
    seed: int

    def as_prompt_context(self) -> dict[str, Any]:
        return {
            "width_px": self.width,
            "height_px": self.height,
            "average_brightness_0_255": round(self.brightness, 1),
            "contrast_stddev": round(self.contrast, 1),
            "edge_density_0_1": round(self.edge_density, 4),
            "dominant_color_hex": self.dominant_hex,
            "aspect_ratio": round(self.aspect_ratio, 2),
        }


@dataclass(frozen=True)
class ProcessedImage:
    raw: bytes
    model_bytes: bytes
    model_mime: str
    original_mime: str
    stats: ImageStats


def _sha_seed(*parts: bytes) -> int:
    digest = hashlib.sha256(b"|".join(parts)).digest()
    return int.from_bytes(digest[:8], "big")


def _stats(image: Image.Image, raw: bytes) -> ImageStats:
    rgba = image.convert("RGB")
    sample = rgba.resize((256, 256), Image.Resampling.LANCZOS)
    gray = sample.convert("L")

    hist = gray.histogram()
    total = sum(hist) or 1
    brightness = sum(index * count for index, count in enumerate(hist)) / total
    mean = brightness
    variance = sum(((index - mean) ** 2) * count for index, count in enumerate(hist)) / total
    contrast = variance**0.5

    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_hist = edges.histogram()
    edge_pixels = sum(edge_hist[40:])
    edge_density = edge_pixels / total

    small = rgba.resize((32, 32), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    avg = tuple(sum(channel) // len(pixels) for channel in zip(*pixels))
    dominant_hex = "#{:02x}{:02x}{:02x}".format(*avg)

    return ImageStats(
        width=image.width,
        height=image.height,
        brightness=brightness,
        contrast=contrast,
        edge_density=edge_density,
        dominant_hex=dominant_hex,
        aspect_ratio=image.width / max(1, image.height),
        seed=_sha_seed(raw, dominant_hex.encode("ascii")),
    )


def decode_image_bytes(raw: bytes, *, content_type: str | None) -> ProcessedImage:
    if not raw:
        raise ImageValidationError(
            "The uploaded image is empty. Please choose a valid JPG, PNG, or WebP file.",
            status_code=422,
        )
    if len(raw) > settings.max_upload_bytes:
        raise ImageValidationError(
            f"Image is too large. Maximum allowed size is {settings.max_upload_mb} MB.",
            status_code=413,
        )
    if content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise ImageValidationError(
            "Unsupported image type. Please upload a JPG, PNG, or WebP image.",
            status_code=415,
        )

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            if image.width < 32 or image.height < 32:
                raise ImageValidationError(
                    "Image resolution is too small. Upload an image at least 32 x 32 pixels.",
                    status_code=422,
                )
            if image.width * image.height > 40_000_000:
                raise ImageValidationError(
                    "Image dimensions are too large. Please resize the image before uploading.",
                    status_code=422,
                )

            display = image.copy()
            if display.mode in {"RGBA", "LA"} or (
                display.mode == "P" and "transparency" in display.info
            ):
                background = Image.new("RGB", display.size, (255, 255, 255))
                converted = display.convert("RGBA")
                background.paste(converted, mask=converted.split()[-1])
                display = background
            else:
                display = display.convert("RGB")

            display = ImageOps.exif_transpose(display)
            display.thumbnail(
                (settings.max_image_edge_px, settings.max_image_edge_px),
                Image.Resampling.LANCZOS,
            )

            output = io.BytesIO()
            display.save(output, format="JPEG", quality=85, optimize=True)
            model_bytes = output.getvalue()
            original_mime = content_type or f"image/{image.format.lower()}" if image.format else "image/jpeg"
            return ProcessedImage(
                raw=raw,
                model_bytes=model_bytes,
                model_mime="image/jpeg",
                original_mime=original_mime,
                stats=_stats(display, raw),
            )
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError(
            "The file could not be read as an image. It may be corrupted or password protected.",
            status_code=422,
        ) from exc


async def process_upload(upload: UploadFile) -> ProcessedImage:
    raw = await upload.read(settings.max_upload_bytes + 1)
    return decode_image_bytes(raw, content_type=upload.content_type)


def random_image_placeholder() -> ImageStats:
    return ImageStats(
        width=0,
        height=0,
        brightness=0.0,
        contrast=0.0,
        edge_density=0.0,
        dominant_hex="#000000",
        aspect_ratio=1.0,
        seed=secrets.randbits(64),
    )
