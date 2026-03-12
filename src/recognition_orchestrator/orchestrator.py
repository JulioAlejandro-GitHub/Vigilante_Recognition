import threading
import time
import os
import cv2
import numpy as np
from typing import Optional

from src.utils.logger import get_logger
from src.recognition_queue.queue import recognition_queue, RecognitionQueue
from src.repositories.recognition_repository import recognition_repository
from src.repositories.camera_repository import camera_repository
from src.db.session import SessionLocal
from src.services.recognition.insightface_service import insightface_service
from src.services.recognition.deepface_service import deepface_service
from src.services.media.storage import storage_service
from src.config.settings import settings
from src.core.enums.domain import ProcessingStatusEnum, SolicitudStatusEnum

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

        # Inicializar motores (lazy loading en primer uso es posible, pero es mejor aquí)
        try:
            insightface_service.initialize()
            deepface_service.initialize()
        except Exception as e:
            logger.error(f"Error inicializando motores: {e}", exc_info=True)

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

        # Inyectar log_context para este thread/job
        log_context = {"camera_id": job.camera_id}
        logger.info(f"Orquestador procesando job: cámara {job.camera_id}", extra=log_context)

        try:

            # Obtener local_id de la cámara para el evento
            camara = camera_repository.get(db, job.camera_id)
            if not camara:
                logger.warning(f"Cámara {job.camera_id} no encontrada en BD. Ignorando job.")
                return

            # Para procesar necesitamos imagen real
            frame_img = None
            if job.frame_data:
                np_arr = np.frombuffer(job.frame_data, np.uint8)
                frame_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if frame_img is None:
                    logger.error(f"Error al decodificar JPEG para la cámara {job.camera_id}. Frame corrupto o vacío.")
                    return
            else:
                # Si no hay data real para test, creamos una vacía, pero fallará la detección
                # frame_img = np.zeros((640, 640, 3), dtype=np.uint8)
                logger.error(f"Error al decodificar JPEG para la cámara {job.camera_id}. Frame corrupto o vacío 2.")
                return

            # 1. Crear Solicitud Recognition (sin img_path por ahora, se puede actualizar luego)
            solicitud = recognition_repository.create_solicitud(
                db=db,
                job=job,
                img_path=None
            )
            logger.debug(f"Creada solicitud de reconocimiento ID: {solicitud.id_solicitud}")

            # 2. Crear Recognition Event (sin imágenes por ahora para obtener el ID)
            event = recognition_repository.create_event(
                db=db,
                solicitud_id=solicitud.id_solicitud,
                camera_id=job.camera_id,
                local_id=camara.local_id,
                job=job,
                frame_img=None,
                frame_image_url=None,
                processing_status=ProcessingStatusEnum.OK # Asumimos OK por ahora
            )
            logger.debug(f"Creado evento de reconocimiento ID: {event.recognition_event_id}")

            # 3. Guardar el frame full ahora que tenemos el event_id
            frame_img_path = None
            frame_img_url = None
            if frame_img is not None:
                # storage_service ahora devuelve (object_key, public_url)
                frame_img_path, frame_img_url = storage_service.save_frame_full(
                    job.camera_id, event.recognition_event_id, job.timestamp, frame_img
                )
                if frame_img_url:
                    # Usamos el object_key (frame_img_path) para compatibilidad con img/frame_img
                    recognition_repository.update_event_images(db, event.recognition_event_id, frame_img_path, frame_img_url)

            # Actualizar también la solicitud por compatibilidad (legacy path o key object)
            if frame_img_path:
                solicitud.img = frame_img_path
                db.commit()

            # 4. Obtener detecciones y galería
            detections = job.metadata.get("detections", []) if job.metadata else []
            gallery = recognition_repository.get_persona_embeddings(db)
            logger.info(f"Galería cargada con {len(gallery)} embeddings.")

            # 5. Crear registro de rostro e invocar engines para cada detección
            face_count = 0
            for face_idx, detection in enumerate(detections, start=1):
                # Extraer bbox y unificar 'box' o 'bbox'
                box_data = None
                if isinstance(detection, dict):
                    box_data = detection.get('box') or detection.get('bbox')
                elif hasattr(detection, 'xyxy'):
                    box_data = detection.xyxy[0].tolist()

                # Recortar el rostro del frame original usando el bbox
                # Se agrega un margen de seguridad para no recortar la barbilla o frente
                face_crop_img = frame_img
                if box_data and len(box_data) >= 4:
                    x1, y1, x2, y2 = map(int, box_data[:4])
                    h, w = frame_img.shape[:2]

                    # Añadir padding del 10%
                    pad_x = int((x2 - x1) * 0.1)
                    pad_y = int((y2 - y1) * 0.1)

                    x1 = max(0, x1 - pad_x)
                    y1 = max(0, y1 - pad_y)
                    x2 = min(w, x2 + pad_x)
                    y2 = min(h, y2 + pad_y)

                    if x2 > x1 and y2 > y1:
                        face_crop_img = frame_img[y1:y2, x1:x2]

                # Guardar crops
                face_img_path = None
                face_img_url = None
                face_preview_path = None
                face_preview_url = None

                if face_crop_img is not None and face_crop_img.size > 0:
                    face_img_path, face_img_url = storage_service.save_face_crop(
                        job.camera_id, event.recognition_event_id, face_idx, job.timestamp, face_crop_img
                    )
                    face_preview_path, face_preview_url = storage_service.save_face_preview(
                        job.camera_id, event.recognition_event_id, face_idx, job.timestamp, face_crop_img
                    )

                # Crear el registro del rostro en la BD
                face = recognition_repository.create_face(
                    db=db,
                    event_id=event.recognition_event_id,
                    face_index=face_idx,
                    box=box_data,
                    face_img=face_img_path,
                    face_preview_img=face_preview_path,
                    face_image_url=face_img_url,
                    face_preview_url=face_preview_url
                )
                face_id = face.recognition_face_id

                # Ejecutar InsightFace como motor principal
                insight_result = insightface_service.process_face(face_crop_img, gallery)
                recognition_repository.save_recognition_engine_result(db, face_id, insight_result)
                logger.info(f"Resultado InsightFace: {insight_result.detected_human}, Similaridad: {insight_result.similarity}")

                final_decision = insight_result

                # Evaluar necesidad de DeepFace (Zona gris / Ambigüedad)
                # Si detectó un humano pero no superó el threshold alto, y está por encima del bajo, es ambiguo.
                # O también si InsightFace por alguna razón falló.
                if insight_result.detected_human and insight_result.similarity is not None:
                    sim = insight_result.similarity
                    if settings.insightface_ambiguous_threshold <= sim < settings.insightface_threshold:
                        logger.info("Resultado ambiguo de InsightFace. Ejecutando DeepFace como fallback...")
                        deep_result = deepface_service.process_face(face_crop_img, gallery)
                        recognition_repository.save_recognition_engine_result(db, face_id, deep_result)
                        logger.info(f"Resultado DeepFace: {deep_result.detected_human}, Similaridad: {deep_result.similarity}")

                        # Si DeepFace da mejor confirmación (supera su threshold), sobreescribir la decisión
                        if deep_result.similarity is not None and deep_result.similarity >= settings.deepface_threshold:
                            final_decision = deep_result
                            logger.info("DeepFace ha confirmado la identidad.")
                        else:
                            logger.info("DeepFace tampoco pudo confirmar contundentemente.")

                # Consolidar decisión final en la tabla recognition_face
                if final_decision.candidate_persona_id:
                    recognition_repository.update_face_with_best_match(db, face_id, final_decision)

                face_count += 1

            logger.info(f"Se crearon {face_count} registros de rostros para el evento {event.recognition_event_id}.")

            # 6. Marcar solicitud como procesada
            recognition_repository.update_solicitud_status(db, solicitud.id_solicitud, SolicitudStatusEnum.PROCESADA)

        except Exception as e:
            db.rollback()
            logger.error(f"Error procesando el job para la cámara {job.camera_id}: {e}", exc_info=True, extra=log_context)
            raise e
        finally:
            db.close()

# Instancia global (Singleton) para esta etapa
orchestrator = RecognitionOrchestrator(recognition_queue)
