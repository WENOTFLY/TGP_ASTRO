"""S3 storage utilities and PDF generation.

This module provides a small wrapper around the :mod:`minio` client used in
the project.  It supports uploading images and PDFs to an S3 compatible
storage (e.g. MinIO) and generating presigned URLs for downloaded files.  HTML
to PDF conversion is performed with `WeasyPrint`_ if it is available in the
runtime environment.

The functions enforce a strict 10 MB limit for all uploaded files as required
by the project specification.

.. _WeasyPrint: https://weasyprint.org/
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from typing import Optional, cast
from uuid import uuid4

from minio import Minio

try:  # pragma: no cover - optional dependency
    from weasyprint import HTML
except Exception:  # pragma: no cover - optional dependency
    HTML = None


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _get_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(f"environment variable {name} is not set")
    return value


@dataclass
class S3Config:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = False

    @classmethod
    def from_env(cls) -> "S3Config":
        """Load configuration from environment variables."""

        secure = os.environ.get("S3_SECURE", "false").lower() == "true"
        return cls(
            endpoint=_get_env("S3_ENDPOINT"),
            access_key=_get_env("S3_ACCESS_KEY"),
            secret_key=_get_env("S3_SECRET_KEY"),
            bucket=_get_env("S3_BUCKET"),
            secure=secure,
        )


class S3Storage:
    """Small helper around :class:`minio.Minio` for file uploads."""

    def __init__(
        self,
        config: Optional[S3Config] = None,
        client: Optional[Minio] = None,
    ) -> None:
        self.config = config or S3Config.from_env()
        self.client = client or Minio(
            self.config.endpoint,
            access_key=self.config.access_key,
            secret_key=self.config.secret_key,
            secure=self.config.secure,
        )

        # Ensure bucket exists only when we created the client ourselves.  This
        # avoids network calls in tests where a dummy client is injected.
        if client is None and not self.client.bucket_exists(self.config.bucket):
            self.client.make_bucket(self.config.bucket)

    # ------------------------------------------------------------------ utils
    def _put_bytes(self, data: bytes, object_name: str, content_type: str) -> str:
        if len(data) > MAX_FILE_SIZE:
            raise ValueError("file too large")

        stream = BytesIO(data)
        self.client.put_object(
            self.config.bucket,
            object_name,
            stream,
            length=len(data),
            content_type=content_type,
        )
        return object_name

    # ----------------------------------------------------------------- public
    def upload_image(
        self,
        data: bytes,
        content_type: str,
        object_name: str | None = None,
    ) -> str:
        """Upload image bytes to S3 and return the object name."""

        object_name = object_name or f"{uuid4().hex}{_guess_extension(content_type)}"
        return self._put_bytes(data, object_name, content_type)

    def upload_pdf_from_html(
        self,
        html: str,
        object_name: str | None = None,
    ) -> str:
        """Render HTML to PDF and upload to S3."""

        if HTML is None:  # pragma: no cover - defensive
            raise RuntimeError("WeasyPrint is not available")

        pdf_bytes = HTML(string=html).write_pdf()
        object_name = object_name or f"{uuid4().hex}.pdf"
        return self._put_bytes(pdf_bytes, object_name, "application/pdf")

    def generate_presigned_url(
        self, object_name: str, expires: timedelta | None = None
    ) -> str:
        """Generate a presigned download URL for a stored object."""

        seconds = int(expires.total_seconds()) if expires else 3600
        return cast(
            str,
            self.client.presigned_get_object(
                self.config.bucket, object_name, expires=seconds
            ),
        )


def _guess_extension(content_type: str) -> str:
    if content_type == "image/png":
        return ".png"
    if content_type in {"image/jpeg", "image/jpg"}:
        return ".jpg"
    return ""


__all__ = ["S3Storage", "S3Config", "MAX_FILE_SIZE"]
