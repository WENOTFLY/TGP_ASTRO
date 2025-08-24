from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from app.core.compose import CardSpec, Layout, compose, save_image


def _card(top: str, bottom: str) -> Image.Image:
    img = Image.new("RGB", (100, 150), top)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 75, 99, 149), fill=bottom)
    return img


def test_row_compose(tmp_path: Path) -> None:
    frame = Image.new("RGBA", (100, 150), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rectangle((0, 0, 99, 149), outline="black")
    watermark = Image.new("RGBA", (20, 10), (255, 0, 0, 255))
    cards = [
        CardSpec(_card("red", "blue"), "A", False),
        CardSpec(_card("red", "green"), "B", True),
    ]
    img = compose(cards, Layout.ROW, frame=frame, watermark=watermark)
    assert img.width == 2 * 100 + 10
    assert img.height > 150
    px = img.getpixel((100 + 10 + 5, 5))
    assert px[:3] == (0, 128, 0) or px[:3] == (0, 255, 0)
    wm_px = img.getpixel((img.width - 10, img.height - 6))
    assert wm_px[0] > wm_px[1]
    data_webp = save_image(img, fmt="WEBP")
    data_jpeg = save_image(img, fmt="JPEG")
    assert len(data_webp) <= 3 * 1024 * 1024
    assert len(data_jpeg) <= 3 * 1024 * 1024


def test_other_layouts() -> None:
    def make_cards(n: int) -> list[CardSpec]:
        return [
            CardSpec(Image.new("RGB", (50, 50), (i, i, i)), None, False)
            for i in range(n)
        ]

    cross_img = compose(make_cards(5), Layout.CROSS)
    assert cross_img.size == (3 * 50 + 2 * 10, 3 * 50 + 2 * 10)

    grid_img = compose(make_cards(9), Layout.GRID_3X3)
    assert grid_img.size == (3 * 50 + 2 * 10, 3 * (50) + 2 * 10)

    gt_img = compose(make_cards(36), Layout.GRAND_TABLEAU)
    assert gt_img.size == (9 * 50 + 8 * 10, 4 * 50 + 3 * 10)

    import pytest

    with pytest.raises(ValueError):
        compose(make_cards(4), Layout.CROSS)
    with pytest.raises(ValueError):
        compose(make_cards(8), Layout.GRID_3X3)
    with pytest.raises(ValueError):
        compose(make_cards(35), Layout.GRAND_TABLEAU)
