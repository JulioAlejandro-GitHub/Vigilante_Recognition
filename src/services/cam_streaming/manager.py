import time
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.repositories.camera_repository import camera_repository
from src.services.yolo_detector.detector import YOLODetector
from src.services.cam_streaming.worker import CameraWorker

logger = get_logger(__name__)

class StreamingManager:
    """
    Gestor principal de cámaras. Lee desde BD y lanza un worker
    concurrente (thread) para el análisis de frames en cada cámara.
    """
    def __init__(self):
        self.workers = {}
        # Usamos una sola instancia de YOLO para optimizar memoria
        # Las llamadas a predict están protegidas por un Lock interno
        self.yolo_detector = YOLODetector(model_name="yolov8n.pt", conf_threshold=0.5)

    def start_streaming(self):
        """
        Consulta las cámaras activas y arranca workers RTSP.
        Crea una sesión temporal para la consulta.
        """
        from src.db.session import SessionLocal
        logger.info("Iniciando StreamingManager. Obteniendo cámaras activas de la BD...")

        db = SessionLocal()
        try:
            active_cameras = camera_repository.get_active_cameras(db)
        finally:
            db.close()

        if not active_cameras:
            logger.warning("No hay cámaras activas en la BD. El StreamingManager está ocioso.")
            return

        logger.info(f"Se encontraron {len(active_cameras)} cámaras activas. Lanzando workers...")

        for camera in active_cameras:
            # Iniciamos el thread de la cámara, compartiendo el detector thread-safe
            worker = CameraWorker(
                camera_model=camera,
                yolo_detector=self.yolo_detector,
                fps_target=5 # Process max 5 FPS to reduce overload
            )

            self.workers[camera.camara_id] = worker
            worker.start()

        logger.info("Todos los workers de streaming han sido iniciados y están procesando en background.")

    def stop_all(self):
        """Detiene todos los workers activamente."""
        logger.info("Deteniendo todos los workers de cámaras...")
        for worker in self.workers.values():
            worker.stop()
            worker.join(timeout=3)

        self.workers.clear()
        logger.info("StreamingManager detenido correctamente.")

streaming_manager = StreamingManager()
