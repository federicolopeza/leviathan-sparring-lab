from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from app.config import get_settings


class MinIOClient:
    async def put_object(self, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    async def delete_object(self, key: str) -> None:
        raise NotImplementedError


class LocalMinIOClient(MinIOClient):
    def __init__(self, cache_dir: str) -> None:
        self.cache_dir = Path(cache_dir)

    async def put_object(self, key: str, data: bytes, content_type: str) -> None:
        path = self.cache_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def delete_object(self, key: str) -> None:
        path = self.cache_dir / key
        try:
            path.unlink()
        except FileNotFoundError:
            pass


class SDKMinIOClient(MinIOClient):
    def __init__(self) -> None:
        from minio import Minio

        settings = get_settings()
        endpoint = settings.MINIO_ENDPOINT
        parsed = urlparse(endpoint)
        secure = parsed.scheme == "https"
        netloc = parsed.netloc or parsed.path
        self._bucket = settings.MINIO_BUCKET
        self._client = Minio(
            netloc,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=secure,
        )

    async def put_object(self, key: str, data: bytes, content_type: str) -> None:
        from io import BytesIO

        self._client.put_object(
            self._bucket,
            key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    async def delete_object(self, key: str) -> None:
        self._client.remove_object(self._bucket, key)


def get_minio_client() -> MinIOClient:
    settings = get_settings()
    if settings.MINIO_ENDPOINT == "local":
        return LocalMinIOClient(settings.MINIO_LOCAL_CACHE_DIR)
    return SDKMinIOClient()
