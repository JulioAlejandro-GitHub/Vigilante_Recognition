from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from src.repositories.base import BaseRepository
from src.repositories.models import SolicitudRecognitionModel, RecognitionEventModel, RecognitionFaceModel, PersonaEmbeddingModel, RecognitionEngineResultModel, ObservedIdentityModel, ObservedIdentityEmbeddingModel, ObservedIdentityLabelHistoryModel
from src.core.models.domain import RecognitionJob
from src.services.recognition.interface import EngineResultContract
from src.core.enums.domain import SolicitudStatusEnum, EstadoEnum, FinalLabelEnum, ProcessingStatusEnum, ObservedStatusEnum, ObservedLabelEnum, RiskLevelEnum
from dateutil.relativedelta import relativedelta
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RecognitionRepository:
    """Repositorio para gestionar solicitudes y eventos de reconocimiento en BD"""

    def create_solicitud(self, db: Session, job: RecognitionJob, img_path: Optional[str] = None) -> SolicitudRecognitionModel:
        """Crea una nueva solicitud de reconocimiento"""
        solicitud = SolicitudRecognitionModel(
            camera_id=job.camera_id,
            source_type=job.source_type,
            source_ref=job.source_ref,
            img=img_path,
            status=SolicitudStatusEnum.PROCESANDO,
            requested_at=job.timestamp
        )
        db.add(solicitud)
        db.commit()
        db.refresh(solicitud)
        return solicitud

    def update_solicitud_status(self, db: Session, solicitud_id: int, status: str) -> Optional[SolicitudRecognitionModel]:
        """Actualiza el estado de una solicitud y establece processed_at si corresponde"""
        solicitud = db.query(SolicitudRecognitionModel).filter(SolicitudRecognitionModel.id_solicitud == solicitud_id).first()
        if solicitud:
            solicitud.status = status
            if status in [SolicitudStatusEnum.PROCESADA, SolicitudStatusEnum.ERROR]:
                solicitud.processed_at = datetime.utcnow()
            db.commit()
            db.refresh(solicitud)
        return solicitud

    def create_event(self, db: Session, solicitud_id: int, camera_id: int, local_id: int, job: RecognitionJob, frame_img: Optional[str] = None, frame_image_url: Optional[str] = None, processing_status: str = ProcessingStatusEnum.OK) -> RecognitionEventModel:
        """Crea un nuevo evento de reconocimiento asociado a una solicitud"""
        event = RecognitionEventModel(
            id_solicitud=solicitud_id,
            camara_id=camera_id,
            local_id=local_id,
            occurred_at=job.timestamp,
            frame_img=frame_img,
            frame_image_url=frame_image_url,
            frame_metadata=job.metadata,
            source_type=job.source_type,
            processing_status=processing_status
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def update_event_images(self, db: Session, event_id: int, frame_img: str, frame_image_url: str) -> None:
        """Actualiza las rutas de imagen del evento después de guardarlas en disco."""
        event = db.query(RecognitionEventModel).filter(RecognitionEventModel.recognition_event_id == event_id).first()
        if event:
            event.frame_img = frame_img
            event.frame_image_url = frame_image_url
            db.commit()
            db.refresh(event)

    def update_event_processing_status(self, db: Session, event_id: int, status: ProcessingStatusEnum) -> None:
        """Actualiza el estado de procesamiento del evento."""
        event = db.query(RecognitionEventModel).filter(RecognitionEventModel.recognition_event_id == event_id).first()
        if event:
            event.processing_status = status
            db.commit()
            db.refresh(event)

    def create_face(self, db: Session, event_id: int, face_index: int = 1, box: Optional[Dict] = None,
                    face_img: Optional[str] = None, face_preview_img: Optional[str] = None,
                    face_image_url: Optional[str] = None, face_preview_url: Optional[str] = None,
                    quality_metrics: Optional[Dict[str, Any]] = None,
                    observed_identity_id: Optional[int] = None) -> RecognitionFaceModel:
        """Crea un registro de rostro detectado para un evento"""
        face = RecognitionFaceModel(
            recognition_event_id=event_id,
            face_index=face_index,
            box=box,
            face_img=face_img,
            face_preview_img=face_preview_img,
            face_image_url=face_image_url,
            face_preview_url=face_preview_url,
            observed_identity_id=observed_identity_id
        )

        if quality_metrics:
            face.face_width = quality_metrics.get("face_width")
            face.face_height = quality_metrics.get("face_height")
            face.blur_score = quality_metrics.get("blur_score")
            face.face_detector_score = quality_metrics.get("face_detector_score")
            face.pose_score = quality_metrics.get("pose_score")
            face.occlusion_score = quality_metrics.get("occlusion_score")
            face.quality_score = quality_metrics.get("quality_score")
            face.perfil = quality_metrics.get("perfil")
            face.discard_reason = quality_metrics.get("discard_reason")

        db.add(face)
        db.commit()
        db.refresh(face)
        return face

    def get_combined_embeddings(self, db: Session) -> List[Dict[str, Any]]:
        """Obtiene la galería combinada de embeddings de personas activas e identidades observadas."""
        # 1. Obtener embeddings de personas enroladas
        persona_query = db.query(PersonaEmbeddingModel).filter(
            PersonaEmbeddingModel.estado == EstadoEnum.ACTIVO
        )

        known_match_mode = settings.known_identity_match_mode
        if known_match_mode == "centroid":
            persona_query = persona_query.filter(PersonaEmbeddingModel.is_centroid == True)
        elif known_match_mode == "topk":
            persona_query = persona_query.filter(PersonaEmbeddingModel.is_representative == True)
        elif known_match_mode == "centroid_plus_topk":
            persona_query = persona_query.filter(
                (PersonaEmbeddingModel.is_centroid == True) |
                (PersonaEmbeddingModel.is_representative == True)
            )

        persona_embeddings = persona_query.all()

        # 2. Obtener embeddings de identidades observadas activas
        query = db.query(ObservedIdentityEmbeddingModel, ObservedIdentityModel).join(
            ObservedIdentityModel, ObservedIdentityModel.observed_identity_id == ObservedIdentityEmbeddingModel.observed_identity_id
        ).filter(
            ObservedIdentityModel.status == ObservedStatusEnum.ACTIVE
        )

        match_mode = settings.observed_identity_match_mode
        if match_mode == "centroid":
            query = query.filter(ObservedIdentityEmbeddingModel.is_centroid == True)
        elif match_mode == "topk":
            query = query.filter(ObservedIdentityEmbeddingModel.is_representative == True)
        elif match_mode == "centroid_plus_topk":
            query = query.filter(
                (ObservedIdentityEmbeddingModel.is_centroid == True) |
                (ObservedIdentityEmbeddingModel.is_representative == True)
            )

        observed_embeddings = query.all()

        gallery = []
        for emb in persona_embeddings:
            gallery.append({
                "persona_id": emb.persona_id,
                "persona_embedding_id": emb.persona_embedding_id,
                "engine": emb.engine,
                "embedding": emb.embedding,
                "is_centroid": emb.is_centroid,
                "is_representative": emb.is_representative
            })

        for emb, obs in observed_embeddings:
            gallery.append({
                "observed_identity_id": emb.observed_identity_id,
                "observed_identity_embedding_id": emb.observed_identity_embedding_id,
                "engine": emb.engine,
                "embedding": emb.embedding_vector,
                "current_label": obs.current_label.value if obs.current_label else ObservedLabelEnum.UNKNOWN.value,
                "risk_level": obs.risk_level.value if obs.risk_level else RiskLevelEnum.LOW.value
            })

        return gallery

    def save_recognition_engine_result(self, db: Session, face_id: int, result: EngineResultContract) -> RecognitionEngineResultModel:
        """Guarda el resultado detallado del motor de reconocimiento para un rostro."""
        engine_result = RecognitionEngineResultModel(
            recognition_face_id=face_id,
            engine=result.engine,
            model_name=result.model_name,
            model_version=result.model_version,
            detected_human=result.detected_human,
            similarity=result.similarity,
            candidate_persona_id=result.candidate_persona_id,
            candidate_persona_embedding_id=result.candidate_persona_embedding_id,
            embedding=result.embedding,
            embedding_dim=result.embedding_dim,
            processing_ms=result.processing_ms,
            raw_response=result.raw_response
        )
        db.add(engine_result)
        db.commit()
        db.refresh(engine_result)
        return engine_result

    def update_face_with_best_match(self, db: Session, face_id: int, result: EngineResultContract, match_type: str = "persona", observed_label: Optional[str] = None) -> None:
        """Actualiza el registro del rostro con la decisión final del orquestador."""
        face = db.query(RecognitionFaceModel).filter(RecognitionFaceModel.recognition_face_id == face_id).first()
        if face:
            if match_type == "persona" and result.candidate_persona_id:
                face.assigned_persona_id = result.candidate_persona_id
                face.final_label = FinalLabelEnum.IDENTIFICADO
            elif match_type == "observed" and result.candidate_observed_id:
                face.observed_identity_id = result.candidate_observed_id

                # Intentamos heredar la etiqueta de la identidad observada
                try:
                    if observed_label and observed_label != ObservedLabelEnum.UNKNOWN.value:
                         face.final_label = FinalLabelEnum(observed_label)
                    else:
                         face.final_label = FinalLabelEnum.DESCONOCIDO
                except ValueError:
                    face.final_label = FinalLabelEnum.DESCONOCIDO

            face.best_similarity = result.similarity
            face.best_engine = result.engine
            db.commit()

    def update_face_with_new_observed_identity(self, db: Session, face_id: int, observed_id: int) -> None:
        """Actualiza el registro del rostro con una nueva identidad observada recién creada."""
        face = db.query(RecognitionFaceModel).filter(RecognitionFaceModel.recognition_face_id == face_id).first()
        if face:
            face.observed_identity_id = observed_id
            face.final_label = FinalLabelEnum.DESCONOCIDO
            db.commit()

    def _calculate_expiration(self, policy: str, from_date: datetime) -> Optional[datetime]:
        """Calcula la fecha de expiración basada en una política"""
        if not policy:
            return None

        try:
            parts = policy.split("_")
            amount = int(parts[0])
            unit = parts[1]

            if unit == "year" or unit == "years":
                return from_date + relativedelta(years=amount)
            elif unit == "month" or unit == "months":
                return from_date + relativedelta(months=amount)
            elif unit == "week" or unit == "weeks":
                return from_date + relativedelta(weeks=amount)
            elif unit == "day" or unit == "days":
                return from_date + relativedelta(days=amount)
        except Exception:
            pass

        return None

    def create_observed_identity(self, db: Session, camera_id: int, face_id: int, image_url: str) -> ObservedIdentityModel:
        """Crea una nueva identidad observada."""
        now = datetime.utcnow()
        policy = settings.default_observed_retention_policy
        expires_at = self._calculate_expiration(policy, now)

        observed = ObservedIdentityModel(
            status=ObservedStatusEnum.ACTIVE,
            current_label=ObservedLabelEnum.UNKNOWN,
            risk_level=RiskLevelEnum.LOW,
            alert_enabled=False,
            last_camera_id=camera_id,
            best_recognition_face_id=face_id,
            best_face_image_url=image_url,
            times_seen=1,
            retention_policy=policy,
            expires_at=expires_at,
            first_seen_at=now,
            last_seen_at=now
        )
        db.add(observed)
        db.commit()
        db.refresh(observed)
        return observed

    def update_observed_identity(self, db: Session, observed_id: int, camera_id: int, timestamp: datetime, face_id: int, image_url: str) -> ObservedIdentityModel:
        """Actualiza una identidad observada existente tras un nuevo match."""
        observed = db.query(ObservedIdentityModel).filter(ObservedIdentityModel.observed_identity_id == observed_id).first()
        if observed:
            observed.times_seen += 1
            observed.last_seen_at = timestamp
            observed.last_camera_id = camera_id
            observed.best_recognition_face_id = face_id
            observed.best_face_image_url = image_url

            # Refrescar expiración
            if observed.retention_policy:
                observed.expires_at = self._calculate_expiration(observed.retention_policy, timestamp)

            db.commit()
            db.refresh(observed)
        return observed

    def update_observed_identity_classification(self, db: Session, observed_id: int, new_label: str, new_risk: str, changed_by: int = None, reason: str = None) -> Optional[ObservedIdentityModel]:
        """Actualiza la clasificación (etiqueta y riesgo) de una identidad observada y deja rastro."""
        observed = db.query(ObservedIdentityModel).filter(ObservedIdentityModel.observed_identity_id == observed_id).first()
        if not observed:
            return None

        old_label = observed.current_label.value if observed.current_label else None
        old_risk = observed.risk_level.value if observed.risk_level else None

        observed.current_label = ObservedLabelEnum(new_label)
        observed.risk_level = RiskLevelEnum(new_risk)

        # Habilitar alertas automáticamente si el riesgo es alto o si es un ladrón/sospechoso
        if new_label in [ObservedLabelEnum.LADRON.value, ObservedLabelEnum.SOSPECHOSO.value, ObservedLabelEnum.PERSONA_INTERES.value] or \
           new_risk in [RiskLevelEnum.HIGH.value, RiskLevelEnum.CRITICAL.value]:
            observed.alert_enabled = True

        history = ObservedIdentityLabelHistoryModel(
            observed_identity_id=observed_id,
            old_label=old_label,
            new_label=new_label,
            old_risk_level=old_risk,
            new_risk_level=new_risk,
            changed_by=changed_by,
            reason=reason
        )
        db.add(history)
        db.commit()
        db.refresh(observed)
        return observed

    def add_persona_embedding_and_update_gallery(self, db: Session, persona_id: int, result: EngineResultContract, quality_score: float, img_origen: Optional[str] = None) -> Optional[PersonaEmbeddingModel]:
        """Añade un nuevo embedding a la persona y actualiza su galería (top-K / centroide)."""
        import numpy as np

        new_embedding = np.array(result.embedding, dtype=np.float32)

        # 1. Obtener embeddings representativos para este motor
        existing_embeddings = db.query(PersonaEmbeddingModel).filter(
            PersonaEmbeddingModel.persona_id == persona_id,
            PersonaEmbeddingModel.engine == result.engine,
            PersonaEmbeddingModel.is_centroid == False,
            PersonaEmbeddingModel.estado == EstadoEnum.ACTIVO
        ).all()

        # 2. Control de duplicidad
        is_duplicate = False
        for emp in existing_embeddings:
            emp_vector = np.array(emp.embedding, dtype=np.float32)
            similarity = np.dot(new_embedding, emp_vector) / (np.linalg.norm(new_embedding) * np.linalg.norm(emp_vector))
            # Usamos el umbral de duplicidad de observados por consistencia, o un valor fijo muy alto
            if similarity >= settings.observed_identity_duplicate_similarity_threshold:
                is_duplicate = True
                logger.info(f"Embedding descartado por redundancia para persona {persona_id} (sim: {similarity:.4f})")
                break

        new_emb_model = None
        if not is_duplicate:
            # 3. Guardar el nuevo embedding (se marca como representativo inicialmente)
            new_emb_model = PersonaEmbeddingModel(
                persona_id=persona_id,
                engine=result.engine,
                model_name=result.model_name,
                embedding_dim=result.embedding_dim,
                embedding=result.embedding,
                img_origen=img_origen,
                quality_score=quality_score,
                is_primary=False,
                is_representative=True,
                is_centroid=False,
                estado=EstadoEnum.ACTIVO
            )
            db.add(new_emb_model)
            db.commit()
            db.refresh(new_emb_model)

        # Independientemente de si se añadió o no, actualizamos la galería para asegurar top-K / centroide
        self.update_persona_gallery(db, persona_id, result.engine)

        return new_emb_model

    def update_persona_gallery(self, db: Session, persona_id: int, engine: str) -> None:
        """Actualiza la galería operacional para una persona conocida (centroide y top-K)."""
        import numpy as np

        # 1. Obtener embeddings existentes para este motor (excluyendo centroide)
        existing_embeddings = db.query(PersonaEmbeddingModel).filter(
            PersonaEmbeddingModel.persona_id == persona_id,
            PersonaEmbeddingModel.engine == engine,
            PersonaEmbeddingModel.is_centroid == False,
            PersonaEmbeddingModel.estado == EstadoEnum.ACTIVO
        ).all()

        if not existing_embeddings:
            return

        embeddings_to_keep = existing_embeddings

        # 2. Seleccionar top-K embeddings representativos y aplicar límites (marcarlos)
        if settings.known_identity_representative_policy == "best_quality":
            # Ordenar por calidad descendente (si no hay, va al final)
            existing_embeddings.sort(key=lambda x: float(x.quality_score) if x.quality_score is not None else -1.0, reverse=True)

            max_embeddings = settings.known_identity_max_embeddings
            embeddings_to_keep = existing_embeddings[:max_embeddings]

            # Todos pasan a no representativos primero
            for emb in existing_embeddings:
                emb.is_representative = False

            # Solo los top-K son representativos
            for emb in embeddings_to_keep:
                emb.is_representative = True

        # 3. Actualizar Centroide (independiente de la política de retención, usar los top-K)
        if settings.known_identity_use_centroid and embeddings_to_keep:
            vectors = [np.array(e.embedding, dtype=np.float32) for e in embeddings_to_keep]
            centroid = np.mean(vectors, axis=0)
            centroid = centroid / np.linalg.norm(centroid) # Normalizar

            centroid_record = db.query(PersonaEmbeddingModel).filter(
                PersonaEmbeddingModel.persona_id == persona_id,
                PersonaEmbeddingModel.engine == engine,
                PersonaEmbeddingModel.is_centroid == True
            ).first()

            if not centroid_record:
                centroid_record = PersonaEmbeddingModel(
                    persona_id=persona_id,
                    engine=engine,
                    model_name=embeddings_to_keep[0].model_name,
                    embedding=centroid.tolist(),
                    embedding_dim=embeddings_to_keep[0].embedding_dim,
                    quality_score=None,
                    is_representative=False,
                    is_centroid=True,
                    estado=EstadoEnum.ACTIVO
                )
                db.add(centroid_record)
            else:
                centroid_record.embedding = centroid.tolist()
                centroid_record.estado = EstadoEnum.ACTIVO

            logger.info(f"Centroide recalculado para persona conocida {persona_id}")

        db.commit()

    def update_observed_identity_gallery(self, db: Session, observed_id: int, face_id: int, result: EngineResultContract, quality_score: float) -> Optional[ObservedIdentityEmbeddingModel]:
        """Actualiza la galería operacional para una identidad observada."""
        import numpy as np

        # 1. Obtener embeddings existentes para este motor (excluyendo centroide por ahora)
        existing_embeddings = db.query(ObservedIdentityEmbeddingModel).filter(
            ObservedIdentityEmbeddingModel.observed_identity_id == observed_id,
            ObservedIdentityEmbeddingModel.engine == result.engine,
            ObservedIdentityEmbeddingModel.is_centroid == False
        ).all()

        new_embedding = np.array(result.embedding, dtype=np.float32)

        # 2. Control de duplicidad (Similarity Threshold)
        is_duplicate = False
        for emp in existing_embeddings:
            emp_vector = np.array(emp.embedding_vector, dtype=np.float32)
            similarity = np.dot(new_embedding, emp_vector) / (np.linalg.norm(new_embedding) * np.linalg.norm(emp_vector))
            if similarity >= settings.observed_identity_duplicate_similarity_threshold:
                is_duplicate = True
                logger.info(f"Embedding descartado por redundancia para identidad observada {observed_id} (sim: {similarity:.4f})")
                break

        new_emb_model = None
        if not is_duplicate:
            # 3. Preparar el nuevo embedding (no se inserta todavía)
            new_emb_model = ObservedIdentityEmbeddingModel(
                observed_identity_id=observed_id,
                recognition_face_id=face_id,
                engine=result.engine,
                model_name=result.model_name,
                embedding_vector=result.embedding,
                embedding_dim=result.embedding_dim,
                quality_score=quality_score,
                is_representative=False
            )
            existing_embeddings.append(new_emb_model)

        embeddings_to_keep = existing_embeddings
        embeddings_to_delete = []

        # 4. Seleccionar top-K embeddings representativos y aplicar límites
        if settings.observed_identity_representative_policy == "best_quality":
            # Ordenar por calidad descendente
            existing_embeddings.sort(key=lambda x: float(x.quality_score) if x.quality_score else 0.0, reverse=True)

            # Mantener máximo K embeddings
            max_embeddings = settings.observed_identity_max_embeddings
            embeddings_to_keep = existing_embeddings[:max_embeddings]
            embeddings_to_delete = existing_embeddings[max_embeddings:]

            # Marcar representativos (por simplificar, los mantenidos son todos representativos)
            for emb in embeddings_to_keep:
                emb.is_representative = True

            for emb in embeddings_to_delete:
                if emb is new_emb_model:
                    # Si el nuevo embedding resulta no entrar en el top-K, no lo agregamos a DB
                    logger.info(f"Embedding nuevo descartado por baja calidad relativa para identidad {observed_id}")
                else:
                    db.delete(emb)
                    logger.info(f"Embedding antiguo descartado por límite de retención para identidad {observed_id}")

        if new_emb_model and new_emb_model in embeddings_to_keep:
            db.add(new_emb_model)
            logger.info(f"Embedding agregado a galería observada para identidad {observed_id}")

        # 5. Actualizar Centroide (independiente de la política de retención)
        if settings.observed_identity_use_centroid and embeddings_to_keep:
            vectors = [np.array(e.embedding_vector, dtype=np.float32) for e in embeddings_to_keep]
            centroid = np.mean(vectors, axis=0)
            centroid = centroid / np.linalg.norm(centroid) # Normalizar

            centroid_record = db.query(ObservedIdentityEmbeddingModel).filter(
                ObservedIdentityEmbeddingModel.observed_identity_id == observed_id,
                ObservedIdentityEmbeddingModel.engine == result.engine,
                ObservedIdentityEmbeddingModel.is_centroid == True
            ).first()

            if not centroid_record:
                centroid_record = ObservedIdentityEmbeddingModel(
                    observed_identity_id=observed_id,
                    recognition_face_id=embeddings_to_keep[0].recognition_face_id,
                    engine=result.engine,
                    model_name=result.model_name,
                    embedding_vector=centroid.tolist(),
                    embedding_dim=result.embedding_dim,
                    quality_score=None,
                    is_representative=False,
                    is_centroid=True
                )
                db.add(centroid_record)
            else:
                centroid_record.embedding_vector = centroid.tolist()

            logger.info(f"Centroide recalculado para identidad {observed_id}")

        db.commit()

        # Evitar hacer db.refresh en un objeto que ha sido eliminado (expunged)
        if new_emb_model and new_emb_model not in embeddings_to_delete:
            db.refresh(new_emb_model)
            return new_emb_model

        return None

recognition_repository = RecognitionRepository()
