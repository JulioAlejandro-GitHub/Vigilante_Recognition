import threading
import time
import os
import cv2
import numpy as np
import time
from typing import Optional

from src.utils.logger import get_logger
from src.recognition_queue.queue import recognition_queue, RecognitionQueue
from src.repositories.recognition_repository import recognition_repository
from src.repositories.camera_repository import camera_repository
from src.db.session import SessionLocal
from src.services.recognition.insightface_service import insightface_service
from src.services.recognition.deepface_service import deepface_service
from src.services.media.storage import storage_service
from src.services.quality.evaluator import face_quality_evaluator, FaceQualityDecision
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
        self._cooldown_cache = {} # Mantiene último timestamp por (camera_id, type, id)

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

    def _is_in_cooldown(self, camera_id: int, identity_type: str, identity_id: int, current_timestamp: float) -> bool:
        if not settings.enable_recognition_camera_suppression:
            return False

        cache_key = f"{camera_id}_{identity_type}_{identity_id}"
        last_seen = self._cooldown_cache.get(cache_key, 0.0)

        # Limpiar entradas antiguas periódicamente no está hecho explícitamente,
        # pero para el thread de vida larga podríamos hacerlo, aunque no es crítico si el dict no crece infinitamente rápido.
        # En una versión robusta se limpiaría el caché de vez en cuando.

        if current_timestamp - last_seen < settings.recognition_camera_suppression_seconds:
            return True

        # Actualizar timestamp
        self._cooldown_cache[cache_key] = current_timestamp
        return False

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

            # Flags y variables diferidas de subida
            frame_img_path = None
            frame_img_url = None
            frame_uploaded = False

            # 3. (Diferido) La subida del frame_full se hará sólo si procesamos un rostro que no esté en cooldown

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

                    # Evaluacion de Calidad
                    quality_metrics = face_quality_evaluator.evaluate(face_crop_img, face_obj)
                    decision = quality_metrics.get("decision")
                    discard_reason = quality_metrics.get("discard_reason")

                    # Log de calidad
                    if decision == FaceQualityDecision.DISCARDED:
                        logger.warning(f"Rostro {face_count} descartado por calidad: {discard_reason}")
                    elif decision == FaceQualityDecision.USABLE_FOR_STORAGE_ONLY:
                        logger.info(f"Rostro {face_count} utilizable solo como evidencia: {discard_reason}")
                    else:
                        logger.info(f"Rostro {face_count} aprobado con score de calidad {quality_metrics.get('quality_score'):.2f}")

                    # Si es totalmente descartado y no queremos guardar basura
                    # Podríamos decidir no guardar la imagen si es muy mala, pero por trazabilidad la guardamos.
                    # Sin embargo, si es DISCARDED, tal vez ni guardamos a disco para ahorrar.
                    # Decisión: Lo guardamos para tener registro de por qué falló o evidencia de intento.

                    # Guardar crops diferido: preparamos variables en None
                    face_img_path = None
                    face_img_url = None
                    face_preview_path = None
                    face_preview_url = None

                    # Extraer el embedding y ejecutar InsightFace para decidir ANTES de subir y guardar en DB
                    start_time = time.time()
                    embedding = face_obj.normed_embedding
                    processing_ms = int((time.time() - start_time) * 1000)

                    # Si la calidad indica que lo descartemos, saltamos totalmente (para no procesarlo ni guardarlo)
                    if decision == FaceQualityDecision.DISCARDED:
                        continue

                    if decision == FaceQualityDecision.USABLE_FOR_STORAGE_ONLY:
                        # No ejecutamos matching. Lo marcaremos para que se suba, pero InsightFace no actúa
                        insight_result = None
                        final_decision = None
                    else:
                        insight_result = insightface_service.match_embedding(embedding, face_obj, gallery, processing_ms)

                        if not insight_result.detected_human:
                            logger.warning(f"InsightFace falló al extraer embedding del rostro {face_count} a pesar de haberlo detectado previamente.")
                            continue

                        logger.info(f"Resultado InsightFace - Rostro {face_count}: Similaridad: {insight_result.similarity}")
                        final_decision = insight_result

                    # Evaluar necesidad de DeepFace y Reglas de decisión (Solo si hubo un final_decision, ie no era USABLE_FOR_STORAGE_ONLY)
                    match_known = False
                    match_observed = False
                    is_suppressed = False
                    obs_label = "unknown"
                    obs_risk = "low"

                    if final_decision:
                        # Evaluar necesidad de DeepFace (Zona gris / Ambigüedad) SOLO PARA CONOCIDOS
                        sim_persona = insight_result.similarity_persona or -1.0
                        if settings.insightface_ambiguous_threshold <= sim_persona < settings.known_person_threshold:
                            logger.info(f"Resultado ambiguo de InsightFace para conocido (sim: {sim_persona:.4f}). Ejecutando DeepFace como fallback...")
                            deep_result = deepface_service.process_face(face_crop_img, gallery)
                            # Nota: no podemos guardar deep_result aún en bd xq face_id no existe, lo guardamos dsp

                            logger.info(f"Resultado DeepFace: {deep_result.detected_human}, Similaridad Persona: {deep_result.similarity_persona}")
                            if deep_result.similarity_persona is not None and deep_result.similarity_persona >= settings.deepface_threshold:
                                final_decision = deep_result
                                logger.info("DeepFace ha confirmado la identidad de la persona conocida.")
                            else:
                                logger.info("DeepFace tampoco pudo confirmar contundentemente al conocido.")

                        # Reglas de decisión explícitas y jerárquicas:
                        final_sim_persona = final_decision.similarity_persona or -1.0
                        final_sim_observed = final_decision.similarity_observed or -1.0
                        current_ts = time.time()

                        # 1. Match con persona conocida
                        if final_decision.candidate_persona_id and final_sim_persona >= settings.known_person_threshold:
                            match_known = True
                            logger.info(f"Match confirmado con persona conocida: {final_decision.candidate_persona_id} (sim: {final_sim_persona:.4f})")

                            # Suprimir por cámara
                            if self._is_in_cooldown(job.camera_id, "persona", final_decision.candidate_persona_id, current_ts):
                                logger.info(f"Supresión por cámara activa para persona conocida {final_decision.candidate_persona_id}. Omitiendo upload y BD.")
                                is_suppressed = True
                                continue # Cortocircuito total: no guardamos NADA, salimos de este rostro

                        # 2. Match con identidad observada
                        if not match_known and settings.enable_observed_identity and final_decision.candidate_observed_id and \
                           final_sim_observed >= settings.observed_identity_threshold:
                            match_observed = True
                            logger.info(f"Match confirmado con identidad observada: {final_decision.candidate_observed_id} (sim: {final_sim_observed:.4f})")

                            # Extraer label y risk
                            obs_label = final_decision.raw_response.get("observed_label", "unknown") if final_decision.raw_response else "unknown"
                            obs_risk = final_decision.raw_response.get("observed_risk", "low") if final_decision.raw_response else "low"

                            # Suprimir por cámara
                            if self._is_in_cooldown(job.camera_id, "observed", final_decision.candidate_observed_id, current_ts):
                                logger.info(f"Supresión por cámara activa para identidad observada {final_decision.candidate_observed_id}. Omitiendo upload y BD.")
                                is_suppressed = True
                                continue # Cortocircuito total: no guardamos NADA, salimos de este rostro

                    # Si llegamos aquí, NO estamos en cooldown. Debemos subir las imágenes y guardar los registros

                    # Subir el frame full SOLAMENTE UNA VEZ por evento y sólo si hay al menos un rostro no suprimido
                    if not frame_uploaded and frame_img is not None:
                        frame_img_path, frame_img_url = storage_service.save_frame_full(
                            job.camera_id, event.recognition_event_id, job.timestamp, frame_img
                        )
                        if frame_img_url:
                            recognition_repository.update_event_images(db, event.recognition_event_id, frame_img_path, frame_img_url)
                        if frame_img_path:
                            solicitud.img = frame_img_path
                            db.commit()
                        frame_uploaded = True

                    # Subir las imágenes del rostro
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
                        face_preview_url=face_preview_url,
                        quality_metrics=quality_metrics
                    )
                    face_id = face_record.recognition_face_id

                    # Si no había decisión (porque era USABLE_FOR_STORAGE_ONLY) terminamos aquí
                    if not final_decision:
                        continue

                    # Guardamos el resultado del motor inicial
                    recognition_repository.save_recognition_engine_result(db, face_id, insight_result)
                    # Si final_decision es distinto (ie. fallback a deepface), guardamos también
                    if final_decision is not insight_result:
                        recognition_repository.save_recognition_engine_result(db, face_id, final_decision)

                    # Aplicar updates en BD para el match (ya que no fue suprimido)
                    if match_known:
                        recognition_repository.update_face_with_best_match(db, face_id, final_decision, match_type="persona")
                    elif match_observed:

                        # ALERTA OPERATIVA si es relevante
                        if obs_label in ['ladron', 'sospechoso', 'persona_interes'] or obs_risk in ['high', 'critical']:
                            logger.warning(f"🚨 ALERTA OPERATIVA GENERADA 🚨 Identidad observada {final_decision.candidate_observed_id} detectada con clasificación: {obs_label} (Riesgo: {obs_risk}) en cámara {job.camera_id}")

                        recognition_repository.update_face_with_best_match(db, face_id, final_decision, match_type="observed", observed_label=obs_label)

                        # Actualizar last_seen y times_seen de la identidad solo si la calidad lo permite
                        quality_score = quality_metrics.get("quality_score", 0.0)
                        if quality_score >= settings.min_quality_score_for_identity_update:
                            recognition_repository.update_observed_identity(
                                db=db,
                                observed_id=final_decision.candidate_observed_id,
                                camera_id=job.camera_id,
                                timestamp=job.timestamp,
                                face_id=face_id,
                                image_url=face_record.face_image_url
                            )
                            # Actualizar galería operacional si supera el umbral estricto
                            if quality_score >= settings.observed_identity_min_quality:
                                logger.info(f"Actualizando galería de observados para la identidad {final_decision.candidate_observed_id}...")
                                recognition_repository.update_observed_identity_gallery(
                                    db=db,
                                    observed_id=final_decision.candidate_observed_id,
                                    face_id=face_id,
                                    result=final_decision,
                                    quality_score=quality_score
                                )
                        else:
                            logger.info("Evitando actualizar identidad observada debido a baja calidad facial del rostro.")

                    # 3. Completamente nuevo: Crear nueva identidad observada
                    if not match_known and not match_observed and settings.enable_observed_identity:
                        quality_score = quality_metrics.get("quality_score", 0.0)
                        if quality_score >= settings.min_quality_score_for_identity_update:
                            logger.info("Creando nueva identidad observada por ausencia de match...")
                            new_observed = recognition_repository.create_observed_identity(
                                db=db,
                                camera_id=job.camera_id,
                                face_id=face_id,
                                image_url=face_record.face_image_url
                            )

                            # Registrar en cooldown usando el ID recién creado para evitar creaciones duplicadas casi instantáneas (aunque yolo agrupa detections)
                            self._is_in_cooldown(job.camera_id, "observed", new_observed.observed_identity_id, current_ts)

                            recognition_repository.update_face_with_new_observed_identity(db, face_id, new_observed.observed_identity_id)

                            # Poblar la galería operacional por primera vez
                            if quality_score >= settings.observed_identity_min_quality:
                                recognition_repository.update_observed_identity_gallery(
                                    db=db,
                                    observed_id=new_observed.observed_identity_id,
                                    face_id=face_id,
                                    result=final_decision,
                                    quality_score=quality_score
                                )
                            else:
                                logger.warning("La identidad observada se creó, pero la calidad no alcanzó para entrar a la galería de embeddings.")
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
