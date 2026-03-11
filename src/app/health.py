import threading
import time
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from src.utils.logger import get_logger
from src.config.settings import settings
from src.db.session import engine
from src.recognition_queue.queue import recognition_queue
from src.services.cam_streaming.manager import streaming_manager

logger = get_logger(__name__)

class HealthMonitor(threading.Thread):
    """
    Monitor de salud en background. Verifica componentes críticos como la
    conexión a la base de datos, el tamaño de la cola de reconocimiento, y
    el estado de los workers de cámaras.
    """
    def __init__(self, interval_seconds: int = 60):
        super().__init__()
        self.interval_seconds = interval_seconds
        self.running = False
        self.daemon = True

    def run(self):
        if not settings.enable_healthcheck:
            logger.info("HealthCheck deshabilitado por configuración.")
            return

        self.running = True
        logger.info(f"Monitor de salud iniciado (intervalo: {self.interval_seconds}s).")

        while self.running:
            time.sleep(self.interval_seconds)

            try:
                self._check_health()
            except Exception as e:
                logger.error(f"Error inesperado durante healthcheck: {e}", exc_info=True)

    def stop(self):
        self.running = False
        logger.info("Monitor de salud detenido.")

    def _check_health(self):
        health_status = {"status": "ok", "db": "ok", "queue": "ok", "workers": "ok"}

        # 1. Check DB Connection
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as e:
            health_status["db"] = "error"
            health_status["status"] = "error"
            logger.error(f"HEALTHCHECK FALLÓ: Sin conexión a base de datos. {e}")

        # 2. Check Queue
        qsize = recognition_queue.qsize()
        if qsize > 500: # Arbitrary warning limit for memory
            health_status["queue"] = "warning"
            logger.warning(f"HEALTHCHECK: Cola de reconocimiento alta ({qsize} items).")

        # 3. Check Camera Workers
        dead_workers = 0
        total_workers = len(streaming_manager.workers)
        for cam_id, worker in streaming_manager.workers.items():
            if not worker.is_alive():
                dead_workers += 1
                logger.warning(f"HEALTHCHECK: Worker de cámara {cam_id} ha muerto.")

        if dead_workers > 0:
            health_status["workers"] = "error"
            health_status["status"] = "error"

        # General status log
        if health_status["status"] == "ok":
            logger.info(f"HEALTHCHECK OK: DB=ok, Queue={qsize}, Workers={total_workers}")
        else:
            logger.warning(f"HEALTHCHECK DEGRADED: {health_status}")

# Instancia global (Singleton)
health_monitor = HealthMonitor(interval_seconds=settings.healthcheck_interval)
