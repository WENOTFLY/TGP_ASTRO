from __future__ import annotations

from typing import Any

import pytest

from app.storage import MAX_FILE_SIZE, S3Config, S3Storage


class DummyMinio:
    """Minimal MinIO stub used for tests."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    # Bucket operations -----------------------------------------------------
    def bucket_exists(self, bucket: str) -> bool:  # pragma: no cover - simple
        return True

    def make_bucket(self, bucket: str) -> None:  # pragma: no cover - simple
        return None

    # Object operations -----------------------------------------------------
    def put_object(
        self,
        bucket: str,
        object_name: str,
        data: Any,
        length: int,
        content_type: str,
    ) -> None:
        self.objects[object_name] = data.read()

    def presigned_get_object(self, bucket: str, object_name: str, expires: int) -> str:
        return f"https://example.com/{bucket}/{object_name}?exp={expires}"


def _storage() -> S3Storage:
    config = S3Config(endpoint="e", access_key="a", secret_key="s", bucket="b")
    return S3Storage(config=config, client=DummyMinio())


def test_upload_image_size_limit() -> None:
    storage = _storage()
    small = b"x" * MAX_FILE_SIZE
    # should succeed
    storage.upload_image(small, "image/png", object_name="img.png")

    big = b"x" * (MAX_FILE_SIZE + 1)
    with pytest.raises(ValueError):
        storage.upload_image(big, "image/png")


def test_generate_presigned_url() -> None:
    storage = _storage()
    url = storage.generate_presigned_url("foo")
    assert "foo" in url


def test_upload_pdf_from_html(monkeypatch: pytest.MonkeyPatch) -> None:
    storage = _storage()

    class DummyHTML:
        def __init__(self, string: str) -> None:
            self.string = string

        def write_pdf(self) -> bytes:
            return b"%PDF-1.4"

    monkeypatch.setattr("app.storage.HTML", DummyHTML)
    name = storage.upload_pdf_from_html("<p>hi</p>")
    assert name.endswith(".pdf")
