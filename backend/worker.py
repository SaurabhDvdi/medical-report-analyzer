import os
import sys
import json
import time
import signal
from datetime import datetime
from dotenv import load_dotenv

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from logging_config import get_logger
from services.queue_service import REPORT_QUEUE_NAME
from routes.reports import process_report
from database import engine, SessionLocal, Base
from models import Report

logger = get_logger("worker")

running = True


def handle_shutdown(signum, frame):
    global running
    logger.info(f"Received termination signal ({signum}). Initiating graceful shutdown...")
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def start_worker():
    """
    Main worker loop consuming OCR and medical report processing tasks from Redis.
    """
    import redis

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"Starting Medical Report OCR/Processing Worker. Connecting to Redis: {redis_url}")

    client = None
    retry_delay = 2.0

    while running and client is None:
        try:
            client = redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=10.0)
            client.ping()
            logger.info("Worker connected to Redis successfully.")
        except Exception as conn_err:
            logger.warning(f"Worker Redis connection failed: {conn_err}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 30.0)

    env = os.getenv("ENVIRONMENT", "development").lower()
    if env in ("production", "staging", "docker") and engine.dialect.name != "mysql":
        logger.critical(f"FATAL: Worker must connect to MySQL in {env} mode, but dialect is '{engine.dialect.name}'")
        raise RuntimeError(f"Worker cannot start with dialect '{engine.dialect.name}' in {env} mode")
    logger.info(f"Worker verified database connection using dialect: {engine.dialect.name}")

    logger.info(f"Worker listening for jobs on queue: '{REPORT_QUEUE_NAME}'")

    while running:
        try:
            # Update heartbeat timestamp for healthcheck monitoring
            try:
                with open("/tmp/worker_heartbeat", "w") as hf:
                    hf.write(str(time.time()))
            except Exception:
                pass

            # Blocking pop with 2s timeout to allow clean shutdown check
            result = client.brpop(REPORT_QUEUE_NAME, timeout=2)
            if result is None:
                continue

            _, raw_payload = result
            job_data = json.loads(raw_payload)
            job_id = job_data.get("job_id", "unknown")
            report_id = job_data.get("report_id")
            file_path = job_data.get("file_path")

            logger.info(f"[WORKER_JOB_START] job_id={job_id} report_id={report_id} file={file_path}")
            t_start = time.perf_counter()

            # Execute existing deterministic extraction + OCR + AI summary pipeline
            process_report(report_id, file_path)

            t_elapsed = time.perf_counter() - t_start
            logger.info(f"[WORKER_JOB_DONE] job_id={job_id} report_id={report_id} elapsed_s={t_elapsed:.2f}")

        except json.JSONDecodeError as json_err:
            logger.error(f"[WORKER_ERROR] Malformed job JSON payload: {json_err}")
        except Exception as loop_err:
            if running:
                logger.error(f"[WORKER_ERROR] Unexpected worker loop exception: {loop_err}", exc_info=True)
                time.sleep(1.0)

    logger.info("Medical Report OCR/Processing Worker terminated cleanly.")


if __name__ == "__main__":
    start_worker()
