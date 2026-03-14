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

            # 4. Obtener detecciones y galería combinada
            detections = job.metadata.get("detections", []) if job.metadata else []
            gallery = recognition_repository.get_combined_embeddings(db)
            logger.info(f"Galería combinada cargada con {len(gallery)} embeddings.")

            # 5. Crear registro de rostro e invocar engines para cada detección de persona
            face_count = 0
            # detections son bboxes de personas
            for person_idx, detection in enumerate(detections, start=1):
                # Extraer bbox de la persona y unificar 'box' o 'bbox'
                person_box = None
                if isinstance(detection, dict):
                    person_box = detection.get('box') or detection.get('bbox')
                elif hasattr(detection, 'xyxy'):
                    person_box = detection.xyxy[0].tolist()

                if not person_box or len(person_box) < 4:
                    logger.warning(f"Bbox de persona inválido en la detección {person_idx}.")
                    continue

                logger.info(f"Persona {person_idx} detectada. Procediendo a detección de rostros en su región.")

                x1, y1, x2, y2 = map(int, person_box[:4])
                h_frame, w_frame = frame_img.shape[:2]

                # Asegurarnos de que el bbox de la persona esté dentro del frame
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w_frame, x2)
                y2 = min(h_frame, y2)

                if x2 <= x1 or y2 <= y1:
                    logger.warning(f"Bbox de persona {person_idx} vacío o fuera del frame. Se ignora.")
                    continue

                # Recortar la persona
                person_crop_img = frame_img[y1:y2, x1:x2]

                # Detectar rostros explícitamente dentro del person_crop
                # Se podría pasar todo el frame, pero al recortar a la persona aseguramos
                # que estamos analizando al sujeto detectado por YOLO
                faces = insightface_service.detect_faces(person_crop_img)

                if not faces:
                    logger.info(f"No se detectaron rostros para la persona {person_idx} (1 persona / 0 rostros). No se forzará reconocimiento falso.")
                    recognition_repository.update_event_processing_status(db, event.recognition_event_id, ProcessingStatusEnum.SIN_ROSTRO)
                    continue

                if len(faces) == 1:
                    logger.info(f"Se detectó 1 rostro válido para la persona {person_idx}.")
                else:
                    logger.info(f"Se detectaron {len(faces)} rostros para la persona {person_idx}. Se procesarán todos (soporte para múltiples rostros).")

                # Procesar cada rostro encontrado en el bbox de la persona
                for sub_face_idx, face_obj in enumerate(faces, start=1):
                    # El bbox devuelto por InsightFace está relativo al person_crop_img
                    # Lo mapeamos al frame original para guardarlo si es necesario
                    face_box = face_obj.bbox.tolist()
                    fx1, fy1, fx2, fy2 = map(int, face_box[:4])

                    face_w = fx2 - fx1
                    face_h = fy2 - fy1

                    if face_w < settings.face_min_width or face_h < settings.face_min_height:
                        logger.warning(f"Bbox facial ({face_w}x{face_h}) menor al mínimo permitido ({settings.face_min_width}x{settings.face_min_height}). Se descarta el rostro.")
                        recognition_repository.update_event_processing_status(db, event.recognition_event_id, ProcessingStatusEnum.FACE_TOO_SMALL)
                        continue

                    # Aplicar padding al rostro
                    pad_x = int(face_w * settings.face_padding_percent)
                    pad_y = int(face_h * settings.face_padding_percent)

                    # Coordenadas relativas al person crop con padding
                    c_fx1 = max(0, fx1 - pad_x)
                    c_fy1 = max(0, fy1 - pad_y)
                    c_fx2 = min(person_crop_img.shape[1], fx2 + pad_x)
                    c_fy2 = min(person_crop_img.shape[0], fy2 + pad_y)

                    if c_fx2 <= c_fx1 or c_fy2 <= c_fy1:
                        logger.warning(f"Crop facial vacío o fuera de rango. Se descarta.")
                        recognition_repository.update_event_processing_status(db, event.recognition_event_id, ProcessingStatusEnum.FACE_CROP_OUT_OF_BOUNDS)
                        continue

                    face_crop_img = person_crop_img[c_fy1:c_fy2, c_fx1:c_fx2]

                    if face_crop_img is None or face_crop_img.size == 0:
                        logger.warning(f"Crop facial vacío o inválido. Se descarta.")
                        recognition_repository.update_event_processing_status(db, event.recognition_event_id, ProcessingStatusEnum.EMPTY_FACE_CROP)
                        continue

                    # Mapear el bbox con padding al frame original para la BD
                    global_box = [x1 + c_fx1, y1 + c_fy1, x1 + c_fx2, y1 + c_fy2]

                    face_count += 1

                    # Guardar crops usando el face_crop REAL
                    face_img_path = None
                    face_img_url = None
                    face_preview_path = None
                    face_preview_url = None

                    face_img_path, face_img_url = storage_service.save_face_crop(
                        job.camera_id, event.recognition_event_id, face_count, job.timestamp, face_crop_img
                    )
                    face_preview_path, face_preview_url = storage_service.save_face_preview(
                        job.camera_id, event.recognition_event_id, face_count, job.timestamp, face_crop_img
                    )

                    # Crear el registro del rostro en la BD
                    face_record = recognition_repository.create_face(
                        db=db,
                        event_id=event.recognition_event_id,
                        face_index=face_count,
                        box=global_box,
                        face_img=face_img_path,
                        face_preview_img=face_preview_path,
                        face_image_url=face_img_url,
                        face_preview_url=face_preview_url
                    )
                    face_id = face_record.recognition_face_id

                    # Ejecutar InsightFace como motor principal sobre el crop del rostro real
                    insight_result = insightface_service.process_face(face_crop_img, gallery)
                    recognition_repository.save_recognition_engine_result(db, face_id, insight_result)

                    if not insight_result.detected_human:
                        logger.warning(f"InsightFace falló al extraer embedding del rostro {face_count} a pesar de haberlo detectado previamente.")
                        continue

                    logger.info(f"Resultado InsightFace - Rostro {face_count}: Similaridad: {insight_result.similarity}")

                    final_decision = insight_result

                    # Evaluar necesidad de DeepFace (Zona gris / Ambigüedad)
                    if insight_result.similarity is not None:
                        sim = insight_result.similarity
                        if settings.insightface_ambiguous_threshold <= sim < settings.known_person_threshold:
                            logger.info("Resultado ambiguo de InsightFace. Ejecutando DeepFace como fallback...")
                            deep_result = deepface_service.process_face(face_crop_img, gallery)
                            recognition_repository.save_recognition_engine_result(db, face_id, deep_result)
                            logger.info(f"Resultado DeepFace: {deep_result.detected_human}, Similaridad: {deep_result.similarity}")

                            if deep_result.similarity is not None and deep_result.similarity >= settings.deepface_threshold:
                                final_decision = deep_result
                                logger.info("DeepFace ha confirmado la identidad.")
                            else:
                                logger.info("DeepFace tampoco pudo confirmar contundentemente.")

                    # Reglas de decisión:
                    # 1. Match con persona conocida
                    match_known = False
                    match_observed = False

                    # Check known
                    if final_decision.candidate_persona_id and final_decision.raw_response and \
                       final_decision.raw_response.get("sim_persona", 0) >= settings.known_person_threshold:
                        match_known = True
                        logger.info(f"Match confirmado con persona conocida: {final_decision.candidate_persona_id}")
                        recognition_repository.update_face_with_best_match(db, face_id, final_decision, match_type="persona")

                    # 2. Match con identidad observada
                    if not match_known and settings.enable_observed_reid and final_decision.candidate_observed_id and \
                       final_decision.raw_response and final_decision.raw_response.get("sim_observed", 0) >= settings.observed_identity_threshold:
                        match_observed = True
                        logger.info(f"Match confirmado con identidad observada: {final_decision.candidate_observed_id}")
                        recognition_repository.update_face_with_best_match(db, face_id, final_decision, match_type="observed")
                        # Actualizar last_seen y times_seen de la identidad
                        recognition_repository.update_observed_identity(
                            db=db,
                            observed_id=final_decision.candidate_observed_id,
                            camera_id=job.camera_id,
                            timestamp=job.timestamp,
                            face_id=face_id,
                            image_url=face_record.face_image_url
                        )

                    # 3. Completamente nuevo: Crear nueva identidad observada
                    if not match_known and not match_observed and settings.enable_observed_reid:
                        # Validar calidad mínima
                        det_score = final_decision.raw_response.get("det_score") if final_decision.raw_response else None
                        if det_score is not None and float(det_score) >= settings.observed_identity_min_quality:
                            logger.info("Creando nueva identidad observada...")
                            new_observed = recognition_repository.create_observed_identity(
                                db=db,
                                camera_id=job.camera_id,
                                face_id=face_id,
                                image_url=face_record.face_image_url
                            )
                            recognition_repository.update_face_with_new_observed_identity(db, face_id, new_observed.observed_identity_id)
                            recognition_repository.create_observed_embedding(db, new_observed.observed_identity_id, face_id, final_decision)
                        else:
                            logger.info("Rostro descartado para nueva identidad observada por baja calidad.")

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
