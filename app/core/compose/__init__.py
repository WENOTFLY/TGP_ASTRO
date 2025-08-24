from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class CardSpec:
    """Card image with optional caption and orientation."""

    image: Image.Image
    caption: str | None = None
    reversed: bool = False


class Layout(str, Enum):
    """Supported collage layouts."""

    ROW = "row"
    GRID_3X3 = "3x3"
    GRAND_TABLEAU = "gt"
    CROSS = "cross"


def _calc_caption_height(cards: Sequence[CardSpec], font: ImageFont.ImageFont) -> int:
    height = 0
    for card in cards:
        if card.caption:
            bbox = font.getbbox(card.caption)
            height = max(height, bbox[3] - bbox[1])
    return height


def compose(
    cards: Sequence[CardSpec],
    layout: Layout | str,
    *,
    frame: Image.Image | None = None,
    watermark: Image.Image | None = None,
    spacing: int = 10,
    font: ImageFont.ImageFont | None = None,
    caption_color: str = "black",
) -> Image.Image:
    """Compose a collage from given card images.

    Args:
        cards: Ordered sequence of card specifications.
        layout: Layout identifier.
        frame: Optional frame overlay per card.
        watermark: Optional watermark for bottom-right corner.
        spacing: Pixel spacing between cards.
        font: Font to use for captions; defaults to PIL default font.
        caption_color: Color for captions.

    Returns:
        Composed PIL image.
    """

    if not cards:
        raise ValueError("No cards provided")
    layout = Layout(layout)
    font = font or ImageFont.load_default()
    card_w, card_h = cards[0].image.size
    cap_h = _calc_caption_height(cards, font)
    cap_extra = cap_h + 5 if cap_h else 0
    cell_w = card_w
    cell_h = card_h + cap_extra

    positions: list[tuple[int, int]]
    cols: int
    rows: int

    if layout is Layout.ROW:
        cols = len(cards)
        rows = 1
        positions = [(i * (cell_w + spacing), 0) for i in range(cols)]
    elif layout is Layout.GRID_3X3:
        if len(cards) != 9:
            raise ValueError("3x3 grid requires 9 cards")
        cols, rows = 3, 3
        positions = [
            (c * (cell_w + spacing), r * (cell_h + spacing))
            for r in range(rows)
            for c in range(cols)
        ]
    elif layout is Layout.GRAND_TABLEAU:
        if len(cards) != 36:
            raise ValueError("Grand Tableau requires 36 cards")
        cols, rows = 9, 4
        positions = [
            (c * (cell_w + spacing), r * (cell_h + spacing))
            for r in range(rows)
            for c in range(cols)
        ]
    elif layout is Layout.CROSS:
        if len(cards) != 5:
            raise ValueError("Cross layout requires 5 cards")
        cols, rows = 3, 3
        grid_pos = [
            (1, 1),  # center
            (1, 0),  # top
            (2, 1),  # right
            (1, 2),  # bottom
            (0, 1),  # left
        ]
        positions = [
            (c * (cell_w + spacing), r * (cell_h + spacing)) for c, r in grid_pos
        ]
    else:
        raise ValueError(f"Unknown layout: {layout}")

    width = cols * cell_w + (cols - 1) * spacing
    height = rows * cell_h + (rows - 1) * spacing
    base = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(base)

    frame_img = None
    if frame:
        if frame.size != (card_w, card_h):
            frame_img = frame.resize((card_w, card_h), Image.LANCZOS)
        else:
            frame_img = frame

    for card, (x, y) in zip(cards, positions, strict=True):
        img = card.image
        if card.reversed:
            img = img.rotate(180, expand=True)
        base.paste(img, (x, y))
        if frame_img:
            base.paste(frame_img, (x, y), frame_img)
        if card.caption:
            bbox = font.getbbox(card.caption)
            tw = bbox[2] - bbox[0]
            tx = x + (card_w - tw) / 2
            ty = y + card_h + 5
            draw.text((tx, ty), card.caption, fill=caption_color, font=font)

    if watermark:
        wm_w, wm_h = watermark.size
        wx = width - wm_w - 5
        wy = height - wm_h - 5
        base.paste(watermark, (wx, wy), watermark)

    return base


def save_image(
    image: Image.Image,
    *,
    fmt: str = "WEBP",
    quality: int = 80,
    max_bytes: int = 3 * 1024 * 1024,
    min_quality: int = 20,
) -> bytes:
    """Save image ensuring file size is under limit by adjusting quality."""

    fmt = fmt.upper()
    if fmt not in {"WEBP", "JPEG"}:
        raise ValueError("fmt must be WEBP or JPEG")
    buffer = BytesIO()
    q = quality
    while q >= min_quality:
        buffer.seek(0)
        buffer.truncate(0)
        if fmt == "JPEG":
            image.convert("RGB").save(buffer, format=fmt, quality=q, optimize=True)
        else:
            image.save(buffer, format=fmt, quality=q)
        if buffer.tell() <= max_bytes:
            break
        q -= 5
    return buffer.getvalue()


__all__ = ["CardSpec", "Layout", "compose", "save_image"]
