import threading
import time
from typing import Optional

from src.utils.logger import get_logger
from src.recognition_queue.queue import recognition_queue, RecognitionQueue
from src.repositories.recognition_repository import recognition_repository
from src.repositories.camera_repository import camera_repository
from src.db.session import SessionLocal

logger = get_logger(__name__)

class RecognitionOrchestrator(threading.Thread):
    """
    Orquestador central del sistema. Consume jobs de la cola,
    los persiste en BD, y prepara el pipeline para el reconocimiento.
    """
    def __init__(self, queue: RecognitionQueue):
        super().__init__()
        self.queue = queue
        self.running = False
        self.daemon = True # Thread dies when main thread dies

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        logger.info("RecognitionOrchestrator iniciado y escuchando la cola...")

        while self.running:
            job = self.queue.get(timeout=1.0)
            if job is None:
                continue

            try:
                self._process_job(job)
            except Exception as e:
                logger.error(f"Error procesando job de la cámara {job.camera_id}: {e}", exc_info=True)
            finally:
                self.queue.task_done()

        logger.info("RecognitionOrchestrator detenido.")

    def _process_job(self, job):
        """
        Lógica de procesamiento por job: persistencia y orquestación.
        """
        db = SessionLocal()
        try:
            logger.info(f"Orquestador procesando job: cámara {job.camera_id}")

            # Obtener local_id de la cámara para el evento
            camara = camera_repository.get(db, job.camera_id)
            if not camara:
                logger.warning(f"Cámara {job.camera_id} no encontrada en BD. Ignorando job.")
                return

            # TODO: Guardar frame_data a disco/S3 y obtener la ruta (simulado por ahora)
            img_path = f"data/frames/{job.camera_id}_{int(job.timestamp.timestamp())}.jpg"
            if job.frame_data:
                # Aquí guardaríamos `job.frame_data` en `img_path`
                pass

            # 1. Crear Solicitud Recognition
            solicitud = recognition_repository.create_solicitud(
                db=db,
                job=job,
                img_path=img_path
            )
            logger.debug(f"Creada solicitud de reconocimiento ID: {solicitud.id_solicitud}")

            # 2. Crear Recognition Event
            event = recognition_repository.create_event(
                db=db,
                solicitud_id=solicitud.id_solicitud,
                camera_id=job.camera_id,
                local_id=camara.local_id,
                job=job,
                frame_img=img_path,
                processing_status='ok' # Asumimos OK por ahora, cambiará si no hay rostros luego
            )
            logger.debug(f"Creado evento de reconocimiento ID: {event.recognition_event_id}")

            # 3. Crear Recognition Face (Placeholder por cada detección de YOLO)
            detections = job.metadata.get("detections", []) if job.metadata else []
            face_count = 0

            # Para la etapa actual, simplemente registramos que hubieron "rostros/personas" detectados
            # y preparamos la BD para los motores de reconocimiento (InsightFace/DeepFace)
            for idx, detection in enumerate(detections, start=1):
                # Extraer bbox si existe en la detección de YOLO
                box = None
                if isinstance(detection, dict) and 'box' in detection:
                    box = detection['box']
                elif hasattr(detection, 'xyxy'):
                    # Formato YOLO ultralytics típico
                    box = {"xyxy": detection.xyxy[0].tolist()}

                face = recognition_repository.create_face(
                    db=db,
                    event_id=event.recognition_event_id,
                    face_index=idx,
                    box=box
                )
                face_count += 1

            logger.info(f"Se crearon {face_count} registros de rostros preliminares para el evento {event.recognition_event_id}.")

            # TODO (Stage 4): Invocar engines (InsightFace/DeepFace)
            # Para cada face_img recortado o pasándole el frame completo,
            # actualizaríamos `RecognitionFaceModel` y crearíamos `RecognitionEngineResult`.

            # 4. Marcar solicitud como procesada
            recognition_repository.update_solicitud_status(db, solicitud.id_solicitud, 'procesada')

        finally:
            db.close()

# Instancia global (Singleton) para esta etapa
orchestrator = RecognitionOrchestrator(recognition_queue)
