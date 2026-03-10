import cv2
import time
import threading
from datetime import datetime
from src.utils.logger import get_logger
from src.services.yolo_detector.detector import YOLODetector
from src.services.cam_streaming.rtsp_builder import build_rtsp_url
from src.core.models.domain import RecognitionJob
from src.recognition_queue.queue import recognition_queue

logger = get_logger(__name__)

class CameraWorker(threading.Thread):
    def __init__(self, camera_model, yolo_detector: YOLODetector, fps_target=5):
        """
        Inicializa el worker de una cámara para leer el stream de manera continua,
        aplicar detección YOLO y generar eventos de reconocimiento.

        :param camera_model: Modelo base de la base de datos `CamaraModel`
        :param yolo_detector: Instancia compartida de YOLODetector
        :param fps_target: Número de frames a procesar por segundo (para reducir redundancia)
        """
        super().__init__()
        self.camera = camera_model
        self.rtsp_url = build_rtsp_url(self.camera)
        self.yolo_detector = yolo_detector

        self.fps_target = fps_target
        self.frame_interval = 1.0 / self.fps_target if self.fps_target > 0 else 0

        self.running = False
        self.cap = None

        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # Cooldown en segundos entre frames útiles enviados

    def connect(self):
        if self.cap is not None:
            self.cap.release()

        logger.info(f"[{self.camera.nombre}] Conectando a stream...")
        self.cap = cv2.VideoCapture(self.rtsp_url)

        if not self.cap.isOpened():
            logger.error(f"[{self.camera.nombre}] Falló la conexión RTSP: {self.rtsp_url}")
            return False

        # Buffer pequeño si está soportado, o configuraciones específicas de backend
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        logger.info(f"[{self.camera.nombre}] Stream abierto correctamente.")
        return True

    def run(self):
        self.running = True

        if not self.rtsp_url:
            logger.error(f"[{self.camera.nombre}] No tiene RTSP URL válida. Finalizando worker.")
            return

        reconnect_delay = 5

        try:
            while self.running:
                if not self.cap or not self.cap.isOpened():
                    success = self.connect()
                    if not success:
                        logger.warning(f"[{self.camera.nombre}] Reintentando en {reconnect_delay} segundos...")
                        time.sleep(reconnect_delay)
                        continue

                # Lectura del frame
                ret, frame = self.cap.read()

                if not ret:
                    logger.warning(f"[{self.camera.nombre}] Error leyendo frame. Intentando reconectar...")
                    self.cap.release()
                    self.cap = None
                    time.sleep(reconnect_delay)
                    continue

                current_time = time.time()

                # Leemos continuamente lo más rápido posible del buffer de FFMPEG/OpenCV para no generar latencia.
                # Solo pasamos a YOLO un frame según el intervalo que decida `self.fps_target`.

                # 1. Filtro FPS: procesar solo un frame por intervalo
                if not hasattr(self, 'last_processed_time'):
                    self.last_processed_time = 0

                if current_time - self.last_processed_time >= self.frame_interval:
                    self.last_processed_time = current_time

                    # YOLO detection on sampled frames
                    # Aplicamos cooldown independiente para no enviar demasiados jobs redundantes de la misma escena a la siguiente etapa
                    if current_time - self.last_detection_time > self.detection_cooldown:
                        detections = self.yolo_detector.detect(frame)

                        if self.yolo_detector.is_relevant_frame(detections):
                            logger.info(f"[{self.camera.nombre}] ¡Personas detectadas! ({len(detections)})")

                            # Generamos candidato para la siguiente etapa
                            job = self._create_recognition_job(frame, detections)

                            # Encolamos el job en la cola de reconocimiento
                            if recognition_queue.put(job, cooldown_seconds=self.detection_cooldown):
                                logger.debug(f"[{self.camera.nombre}] Job candidato encolado exitosamente.")
                                self.last_detection_time = current_time
                            else:
                                logger.debug(f"[{self.camera.nombre}] Job ignorado o cola llena.")
        finally:
            if self.cap:
                self.cap.release()
                logger.info(f"[{self.camera.nombre}] Worker detenido, recursos liberados.")

    def _create_recognition_job(self, frame, detections) -> RecognitionJob:
        # Encodeamos el frame como JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        return RecognitionJob(
            camera_id=self.camera.camara_id,
            source_type="camera",
            source_ref=self.rtsp_url,
            frame_data=frame_bytes,
            timestamp=datetime.utcnow(),
            metadata={
                "source": self.camera.nombre,
                "detections": detections,
                "stage": "early_detection_yolo"
            }
        )

    def stop(self):
        logger.info(f"[{self.camera.nombre}] Solicitando detención del worker...")
        self.running = False
