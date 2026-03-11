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

        # Diccionario base para inyectar en logger extra
        self.log_extra = {"camera_id": self.camera.camara_id}

    def connect(self):
        if self.cap is not None:
            self.cap.release()

        logger.info(f"Conectando a stream... ({self.camera.nombre})", extra=self.log_extra)
        self.cap = cv2.VideoCapture(self.rtsp_url)

        if not self.cap.isOpened():
            logger.error(f"Falló la conexión RTSP: {self.rtsp_url}", extra=self.log_extra)
            return False

        # Buffer pequeño si está soportado, o configuraciones específicas de backend
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        logger.info(f"Stream abierto correctamente. ({self.camera.nombre})", extra=self.log_extra)
        return True

    def run(self):
        self.running = True

        if not self.rtsp_url:
            logger.error(f"No tiene RTSP URL válida. Finalizando worker. ({self.camera.nombre})", extra=self.log_extra)
            return

        reconnect_delay = 5
        max_reconnect_delay = 60 # Max 1 minute
        consecutive_failures = 0

        try:
            while self.running:
                try:
                    if not self.cap or not self.cap.isOpened():
                        success = self.connect()
                        if not success:
                            consecutive_failures += 1
                            current_delay = min(reconnect_delay * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
                            logger.warning(f"Reintentando en {current_delay} segundos... ({self.camera.nombre})", extra=self.log_extra)
                            time.sleep(current_delay)
                            continue
                        else:
                            consecutive_failures = 0

                    # Lectura del frame
                    ret, frame = self.cap.read()

                    if not ret:
                        logger.warning(f"Error leyendo frame. Intentando reconectar... ({self.camera.nombre})", extra=self.log_extra)
                        if self.cap:
                            self.cap.release()
                        self.cap = None
                        consecutive_failures += 1
                        current_delay = min(reconnect_delay * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
                        time.sleep(current_delay)
                        continue
                    else:
                        consecutive_failures = 0

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
                                logger.info(f"¡Personas detectadas! ({len(detections)}) ({self.camera.nombre})", extra=self.log_extra)

                                # Generamos candidato para la siguiente etapa
                                job = self._create_recognition_job(frame, detections)

                                # Encolamos el job en la cola de reconocimiento
                                if recognition_queue.put(job, cooldown_seconds=self.detection_cooldown):
                                    logger.debug(f"Job candidato encolado exitosamente. ({self.camera.nombre})", extra=self.log_extra)
                                    self.last_detection_time = current_time
                                else:
                                    logger.debug(f"Job ignorado o cola llena. ({self.camera.nombre})", extra=self.log_extra)

                except Exception as inner_e:
                    logger.error(f"Error procesando frame en CameraWorker: {inner_e}", exc_info=True, extra=self.log_extra)
                    time.sleep(1) # Prevenir busy-loop si el error es persistente

        except Exception as e:
            logger.critical(f"Error fatal y no recuperable en CameraWorker: {e}", exc_info=True, extra=self.log_extra)
        finally:
            if self.cap:
                self.cap.release()
                logger.info(f"Worker detenido, recursos liberados. ({self.camera.nombre})", extra=self.log_extra)

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
        logger.info(f"Solicitando detención del worker... ({self.camera.nombre})", extra=self.log_extra)
        self.running = False
