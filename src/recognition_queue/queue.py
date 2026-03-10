import queue
from src.core.models.domain import RecognitionJob
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RecognitionQueue:
    """
    Cola en memoria para almacenar trabajos de reconocimiento.
    Desacopla la detección (YOLO) del procesamiento pesado.
    """
    def __init__(self, maxsize: int = 1000):
        self._queue = queue.Queue(maxsize=maxsize)
        self._last_processed = {}  # camera_id -> timestamp para evitar repeticiones obvias

    def put(self, job: RecognitionJob, cooldown_seconds: float = 1.0) -> bool:
        """
        Añade un trabajo a la cola si pasa el filtro de cooldown.
        """
        camera_id = job.camera_id
        current_time = job.timestamp.timestamp()

        # Filtro de repetición obvia: si la misma cámara manda un evento muy rápido, ignorar
        last_time = self._last_processed.get(camera_id, 0)
        if current_time - last_time < cooldown_seconds:
            logger.debug(f"Job ignorado por cooldown. Cámara: {camera_id}")
            return False

        try:
            self._queue.put(job, block=False)
            self._last_processed[camera_id] = current_time
            logger.debug(f"Job encolado exitosamente. Cámara: {camera_id}. Tamaño cola: {self._queue.qsize()}")
            return True
        except queue.Full:
            logger.error(f"La cola de reconocimiento está llena (max={self._queue.maxsize}). Job descartado.")
            return False

    def get(self, timeout: float = 1.0) -> RecognitionJob | None:
        """
        Obtiene un trabajo de la cola de manera bloqueante con timeout.
        """
        try:
            job = self._queue.get(block=True, timeout=timeout)
            return job
        except queue.Empty:
            return None

    def task_done(self):
        """
        Indica que el último trabajo obtenido fue procesado.
        """
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()

# Instancia global (Singleton) para esta etapa en memoria
recognition_queue = RecognitionQueue()
