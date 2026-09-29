import os
import json
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from logging_config import get_logger

logger = get_logger(__name__)

REPORT_QUEUE_NAME = "medical:queue:report_processing"


class BaseQueueService(ABC):
    """Abstract interface for background report processing task queue."""

    @abstractmethod
    def enqueue_report_processing(self, report_id: int, file_path: str) -> str:
        """
        Enqueues report processing task and returns a unique job ID.
        """
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Checks health and reachability of queue broker.
        """
        pass

    @abstractmethod
    def get_queue_length(self) -> int:
        """
        Returns number of pending jobs in queue.
        """
        pass


class RedisQueueService(BaseQueueService):
    """
    Production Redis queue service for distributing OCR and clinical processing jobs.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import redis
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            self._client.ping()
            logger.info(f"RedisQueueService connected successfully to: {self.redis_url}")
        except Exception as e:
            logger.warning(f"RedisQueueService could not connect to {self.redis_url}: {e}. Queue operations will fallback.")
            self._client = None

    def is_healthy(self) -> bool:
        if not self._client:
            return False
        try:
            return bool(self._client.ping())
        except Exception:
            return False

    def enqueue_report_processing(self, report_id: int, file_path: str) -> str:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        payload = {
            "job_id": job_id,
            "report_id": report_id,
            "file_path": file_path,
            "enqueued_at": datetime.utcnow().isoformat()
        }

        if self._client:
            try:
                self._client.lpush(REPORT_QUEUE_NAME, json.dumps(payload))
                logger.info(f"[QUEUE] Enqueued report_id={report_id} job_id={job_id} to {REPORT_QUEUE_NAME}")
                return job_id
            except Exception as e:
                logger.error(f"[QUEUE_ERROR] Failed to push to Redis queue: {e}")
                raise RuntimeError(f"Queue delivery failed: {e}")
        else:
            raise RuntimeError(f"Redis client not connected to {self.redis_url}")

    def get_queue_length(self) -> int:
        if self._client:
            try:
                return self._client.llen(REPORT_QUEUE_NAME)
            except Exception:
                return 0
        return 0


class InMemoryQueueService(BaseQueueService):
    """
    In-memory fallback queue for local development and environments without Redis.
    """

    def __init__(self):
        self._jobs = []
        logger.info("InMemoryQueueService active (synchronous / local mode).")

    def is_healthy(self) -> bool:
        return True

    def enqueue_report_processing(self, report_id: int, file_path: str) -> str:
        job_id = f"local_job_{uuid.uuid4().hex[:12]}"
        self._jobs.append({"job_id": job_id, "report_id": report_id, "file_path": file_path})
        logger.info(f"[IN_MEMORY_QUEUE] Registered job {job_id} for report {report_id}")
        return job_id

    def get_queue_length(self) -> int:
        return len(self._jobs)


# Singleton factory
_queue_service_instance: Optional[BaseQueueService] = None


def get_queue_service() -> BaseQueueService:
    """
    Factory resolving queue service based on ASYNC_PROCESSING_ENABLED and REDIS_URL.
    """
    global _queue_service_instance
    if _queue_service_instance is None:
        async_enabled = os.getenv("ASYNC_PROCESSING_ENABLED", "false").lower() in ("true", "1", "yes")
        if async_enabled:
            redis_svc = RedisQueueService()
            if redis_svc.is_healthy():
                _queue_service_instance = redis_svc
            else:
                logger.warning("ASYNC_PROCESSING_ENABLED is true but Redis is unreachable; falling back to InMemoryQueueService.")
                _queue_service_instance = InMemoryQueueService()
        else:
            _queue_service_instance = InMemoryQueueService()
    return _queue_service_instance
