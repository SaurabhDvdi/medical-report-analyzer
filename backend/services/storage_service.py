import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from typing import Optional
from logging_config import get_logger

logger = get_logger(__name__)


class BaseStorageService(ABC):
    """Abstract storage interface for medical report file persistence."""

    @abstractmethod
    def save_file(self, content: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """
        Persists file content and returns a storage key / path identifier.
        """
        pass

    @abstractmethod
    def get_file(self, storage_key: str) -> bytes:
        """
        Retrieves binary file content given a storage key.
        """
        pass

    @abstractmethod
    def get_local_path(self, storage_key: str) -> str:
        """
        Returns a local filesystem path suitable for tools requiring local paths (OCR/PDF).
        For remote storage, ensures the file is temporarily cached locally.
        """
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """
        Deletes a stored file.
        """
        pass

    @abstractmethod
    def file_exists(self, storage_key: str) -> bool:
        """
        Checks whether a file exists in the storage provider.
        """
        pass


class LocalStorageService(BaseStorageService):
    """
    Local filesystem / Kubernetes PVC storage backend.
    Files are stored in a dedicated persistent volume directory.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.getenv("STORAGE_LOCAL_PATH", "uploads")
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"LocalStorageService initialized at: {os.path.abspath(self.base_dir)}")

    def _resolve_path(self, storage_key: str) -> str:
        # Prevent directory traversal attacks
        safe_key = os.path.basename(storage_key.replace("\\", "/"))
        # Check if storage_key already starts with base_dir
        if storage_key.startswith(self.base_dir):
            return storage_key
        return os.path.join(self.base_dir, safe_key)

    def save_file(self, content: bytes, filename: str, content_type: Optional[str] = None) -> str:
        target_path = self._resolve_path(filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)
        return target_path

    def get_file(self, storage_key: str) -> bytes:
        target_path = self.get_local_path(storage_key)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Report file not found: {storage_key}")
        with open(target_path, "rb") as f:
            return f.read()

    def get_local_path(self, storage_key: str) -> str:
        if os.path.exists(storage_key):
            return storage_key
        resolved = self._resolve_path(storage_key)
        if os.path.exists(resolved):
            return resolved
        # Check backend/ relative path fallback for tests
        alt_path = os.path.join("backend", resolved)
        if os.path.exists(alt_path):
            return alt_path
        return resolved

    def delete_file(self, storage_key: str) -> bool:
        target_path = self.get_local_path(storage_key)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                return True
            except Exception as e:
                logger.error(f"Error deleting file {target_path}: {e}")
                return False
        return False

    def file_exists(self, storage_key: str) -> bool:
        target_path = self.get_local_path(storage_key)
        return os.path.exists(target_path)


class S3StorageService(BaseStorageService):
    """
    S3-compatible Object Storage Service (AWS S3, MinIO, GCP Cloud Storage S3 API).
    Seamlessly interacts with cloud bucket while providing a local caching layer for OCR.
    """

    def __init__(self):
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL") or None
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "medical-reports-storage")
        self.access_key = os.getenv("S3_ACCESS_KEY", "")
        self.secret_key = os.getenv("S3_SECRET_KEY", "")
        self.region = os.getenv("S3_REGION", "us-east-1")
        self.local_cache_dir = os.path.join(tempfile.gettempdir(), "medical_s3_cache")
        os.makedirs(self.local_cache_dir, exist_ok=True)

        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import boto3
            from botocore.client import Config
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version="s3v4")
            )
            logger.info(f"S3StorageService initialized for bucket: {self.bucket_name}")
        except ImportError:
            logger.warning("boto3 is not installed. S3StorageService operations will fallback to local cache.")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self._client = None

    def save_file(self, content: bytes, filename: str, content_type: Optional[str] = None) -> str:
        safe_key = f"reports/{os.path.basename(filename)}"
        if self._client:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            import io
            self._client.upload_fileobj(io.BytesIO(content), self.bucket_name, safe_key, ExtraArgs=extra_args)
            logger.info(f"Uploaded file to S3: {self.bucket_name}/{safe_key}")
        
        # Also cache locally for immediate OCR pipeline access
        cache_path = os.path.join(self.local_cache_dir, os.path.basename(filename))
        with open(cache_path, "wb") as f:
            f.write(content)

        return safe_key

    def get_file(self, storage_key: str) -> bytes:
        if self._client:
            import io
            buffer = io.BytesIO()
            self._client.download_fileobj(self.bucket_name, storage_key, buffer)
            buffer.seek(0)
            return buffer.read()
        else:
            cache_path = os.path.join(self.local_cache_dir, os.path.basename(storage_key))
            if os.path.exists(cache_path):
                with open(cache_path, "rb") as f:
                    return f.read()
            raise RuntimeError("S3 client not initialized and file not in local cache.")

    def get_local_path(self, storage_key: str) -> str:
        cache_path = os.path.join(self.local_cache_dir, os.path.basename(storage_key))
        if os.path.exists(cache_path):
            return cache_path

        if self._client:
            self._client.download_file(self.bucket_name, storage_key, cache_path)
            return cache_path

        return cache_path

    def delete_file(self, storage_key: str) -> bool:
        if self._client:
            try:
                self._client.delete_object(Bucket=self.bucket_name, Key=storage_key)
                return True
            except Exception as e:
                logger.error(f"Failed to delete S3 object {storage_key}: {e}")
                return False
        cache_path = os.path.join(self.local_cache_dir, os.path.basename(storage_key))
        if os.path.exists(cache_path):
            os.remove(cache_path)
            return True
        return False

    def file_exists(self, storage_key: str) -> bool:
        if self._client:
            try:
                self._client.head_object(Bucket=self.bucket_name, Key=storage_key)
                return True
            except Exception:
                return False
        cache_path = os.path.join(self.local_cache_dir, os.path.basename(storage_key))
        return os.path.exists(cache_path)


# Singleton factory
_storage_service_instance: Optional[BaseStorageService] = None


def get_storage_service() -> BaseStorageService:
    """
    Factory resolving the active storage service based on STORAGE_BACKEND.
    Defaults to LocalStorageService for local Docker / Kubernetes PVC.
    """
    global _storage_service_instance
    if _storage_service_instance is None:
        backend_type = os.getenv("STORAGE_BACKEND", "local").lower().strip()
        if backend_type == "s3" and os.getenv("S3_BUCKET_NAME"):
            _storage_service_instance = S3StorageService()
        else:
            _storage_service_instance = LocalStorageService()
    return _storage_service_instance
