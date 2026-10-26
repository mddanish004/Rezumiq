"""Object storage, ported from lib/storage.ts.

Two drivers: local disk (dev) and Cloudflare R2 (prod, S3-compatible). The
public surface mirrors the TS Storage interface so the compile cache and the
backups port can call it unchanged.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _settings():
    from django.conf import settings as s

    return s


try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception


def assert_deletable_prefix(prefix: str) -> None:
    trimmed = prefix.strip()
    if not trimmed or all(c == "/" for c in trimmed):
        raise ValueError("Refusing to delete with an empty storage prefix")


def stale_keys(objects: list[dict[str, Any]], cutoff: datetime) -> list[str]:
    return [o["key"] for o in objects if o["modifiedAt"] < cutoff]


def _utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def _path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root)):
            raise ValueError(f"Invalid storage key: {key}")
        return path

    def put(self, key: str, body: bytes, content_type: str = "application/octet-stream") -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    def get(self, key: str) -> bytes | None:
        try:
            return self._path_for(key).read_bytes()
        except FileNotFoundError:
            return None

    def delete_prefix(self, prefix: str) -> None:
        assert_deletable_prefix(prefix)
        import shutil

        target = self._path_for(prefix)
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()

    def delete_older(self, prefix: str, cutoff: datetime) -> int:
        assert_deletable_prefix(prefix)

        cutoff = _utc(cutoff)
        dir_path = self._path_for(prefix)
        try:
            names = [n for n in dir_path.iterdir()]
        except (FileNotFoundError, NotADirectoryError):
            return 0
        stale: list[str] = []
        infos: list[dict] = []
        for entry in names:
            if entry.is_file():
                infos.append(
                    {
                        "key": entry.name,
                        "modifiedAt": _utc(datetime.fromtimestamp(entry.stat().st_mtime, tz=UTC)),
                    }
                )
        for o in infos:
            if o["modifiedAt"] < cutoff:
                stale.append(o["key"])
        for name in stale:
            (dir_path / name).unlink(missing_ok=True)
        return len(stale)

    def latest(self, prefix: str) -> dict[str, Any] | None:
        dir_path = self._path_for(prefix)
        try:
            names = sorted(n.name for n in dir_path.iterdir() if n.is_file())
        except (FileNotFoundError, NotADirectoryError):
            return None
        if not names:
            return None
        name = names[-1]
        info = (dir_path / name).stat()
        return {
            "key": f"{prefix}{name}",
            "sizeBytes": info.st_size,
            "modifiedAt": _utc(datetime.fromtimestamp(info.st_mtime, tz=UTC)),
        }


class R2Storage:
    def __init__(self) -> None:
        if boto3 is None:
            raise RuntimeError("boto3 is required for the r2 storage driver")
        s = _settings()
        self.bucket = s.R2_BUCKET
        self.client = boto3.client(
            "s3",
            region_name="auto",
            endpoint_url=f"https://{s.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=s.R2_ACCESS_KEY_ID,
            aws_secret_access_key=s.R2_SECRET_ACCESS_KEY,
        )

    def put(self, key: str, body: bytes, content_type: str = "application/octet-stream") -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType=content_type)

    def get(self, key: str) -> bytes | None:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                return None
            raise

    def _list_pages(self, prefix: str):
        token = None
        while True:
            kwargs = {"Bucket": self.bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            page = self.client.list_objects_v2(**kwargs)
            yield page
            token = page.get("NextContinuationToken") if page.get("IsTruncated") else None
            if not token:
                break

    def delete_prefix(self, prefix: str) -> None:
        assert_deletable_prefix(prefix)
        failed = 0
        for page in self._list_pages(prefix):
            objects = [{"Key": o["Key"]} for o in (page.get("Contents") or [])]
            if not objects:
                continue
            resp = self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects})
            for err in resp.get("Errors") or []:
                failed += 1
        if failed:
            raise RuntimeError(f"{failed} storage objects under {prefix} could not be deleted")

    def delete_older(self, prefix: str, cutoff: datetime) -> int:
        assert_deletable_prefix(prefix)
        cutoff = _utc(cutoff)
        deleted = 0
        failed = 0
        for page in self._list_pages(prefix):
            stale = [
                o["Key"] for o in (page.get("Contents") or []) if _utc(o["LastModified"]) < cutoff
            ]
            if not stale:
                continue
            resp = self.client.delete_objects(
                Bucket=self.bucket, Delete={"Objects": [{"Key": k} for k in stale]}
            )
            failed += len(resp.get("Errors") or [])
            deleted += len(stale) - len(resp.get("Errors") or [])
        if failed:
            raise RuntimeError(
                f"{failed} stale storage objects under {prefix} could not be deleted"
            )
        return deleted

    def latest(self, prefix: str) -> dict[str, Any] | None:
        newest: dict[str, Any] | None = None
        for page in self._list_pages(prefix):
            contents = page.get("Contents") or []
            if not contents:
                continue
            last = contents[-1]
            newest = {
                "key": last["Key"],
                "sizeBytes": last.get("Size", 0),
                "modifiedAt": _utc(last["LastModified"]),
            }
        return newest


def get_storage():
    s = _settings()
    driver = getattr(s, "STORAGE_DRIVER", "local")
    if driver == "r2":
        return R2Storage()
    return LocalStorage(getattr(s, "LOCAL_STORAGE_DIR", str(Path.cwd() / "storage")))


class _LazyStorage:
    def __init__(self) -> None:
        self._instance = None

    def _real(self):
        if self._instance is None:
            self._instance = get_storage()
        return self._instance

    def __getattr__(self, name):
        return getattr(self._real(), name)


storage = _LazyStorage()
