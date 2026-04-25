from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from app.config import get_settings


class MinIOClient:
    async def get_object(self, key: str) -> bytes:
        raise NotImplementedError


class LocalMinIOClient(MinIOClient):
    def __init__(self, cache_dir: str) -> None:
        self.cache_dir = Path(cache_dir)

    async def get_object(self, key: str) -> bytes:
        return (self.cache_dir / key).read_bytes()


class SDKMinIOClient(MinIOClient):
    def __init__(self) -> None:
        from minio import Minio

        settings = get_settings()
        parsed = urlparse(settings.MINIO_ENDPOINT)
        secure = parsed.scheme == "https"
        netloc = parsed.netloc or parsed.path
        self._bucket = settings.MINIO_BUCKET
        self._client = Minio(
            netloc,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=secure,
        )

    async def get_object(self, key: str) -> bytes:
        response = self._client.get_object(self._bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


def get_minio_client() -> MinIOClient:
    settings = get_settings()
    if settings.MINIO_ENDPOINT == "local":
        return LocalMinIOClient(settings.MINIO_LOCAL_CACHE_DIR)
    return SDKMinIOClient()
