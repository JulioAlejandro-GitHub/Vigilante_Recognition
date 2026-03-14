from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from src.repositories.base import BaseRepository
from src.repositories.models import SolicitudRecognitionModel, RecognitionEventModel, RecognitionFaceModel, PersonaEmbeddingModel, RecognitionEngineResultModel, ObservedIdentityModel, ObservedIdentityEmbeddingModel
from src.core.models.domain import RecognitionJob
from src.services.recognition.interface import EngineResultContract
from src.core.enums.domain import SolicitudStatusEnum, EstadoEnum, FinalLabelEnum, ProcessingStatusEnum, ObservedStatusEnum

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
                    face_image_url: Optional[str] = None, face_preview_url: Optional[str] = None) -> RecognitionFaceModel:
        """Crea un registro de rostro detectado para un evento"""
        face = RecognitionFaceModel(
            recognition_event_id=event_id,
            face_index=face_index,
            box=box,
            face_img=face_img,
            face_preview_img=face_preview_img,
            face_image_url=face_image_url,
            face_preview_url=face_preview_url
        )
        db.add(face)
        db.commit()
        db.refresh(face)
        return face

    def get_combined_embeddings(self, db: Session) -> List[Dict[str, Any]]:
        """Obtiene la galería combinada de embeddings de personas activas e identidades observadas."""
        # 1. Obtener embeddings de personas enroladas
        persona_embeddings = db.query(PersonaEmbeddingModel).filter(
            PersonaEmbeddingModel.estado == EstadoEnum.ACTIVO
        ).all()

        # 2. Obtener embeddings de identidades observadas activas
        observed_embeddings = db.query(ObservedIdentityEmbeddingModel).join(
            ObservedIdentityModel, ObservedIdentityModel.observed_identity_id == ObservedIdentityEmbeddingModel.observed_identity_id
        ).filter(
            ObservedIdentityModel.status == ObservedStatusEnum.ACTIVE
        ).all()

        gallery = []
        for emb in persona_embeddings:
            gallery.append({
                "persona_id": emb.persona_id,
                "persona_embedding_id": emb.persona_embedding_id,
                "engine": emb.engine,
                "embedding": emb.embedding
            })

        for emb in observed_embeddings:
            gallery.append({
                "observed_identity_id": emb.observed_identity_id,
                "observed_identity_embedding_id": emb.observed_identity_embedding_id,
                "engine": emb.engine,
                "embedding": emb.embedding_vector
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

    def update_face_with_best_match(self, db: Session, face_id: int, result: EngineResultContract, match_type: str = "persona") -> None:
        """Actualiza el registro del rostro con la decisión final del orquestador."""
        face = db.query(RecognitionFaceModel).filter(RecognitionFaceModel.recognition_face_id == face_id).first()
        if face:
            if match_type == "persona" and result.candidate_persona_id:
                face.assigned_persona_id = result.candidate_persona_id
                face.final_label = FinalLabelEnum.IDENTIFICADO
            elif match_type == "observed" and result.candidate_observed_id:
                face.observed_identity_id = result.candidate_observed_id
                # Si es observado, sigue siendo desconocido pero con trazabilidad
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

    def create_observed_identity(self, db: Session, camera_id: int, face_id: int, image_url: str) -> ObservedIdentityModel:
        """Crea una nueva identidad observada."""
        observed = ObservedIdentityModel(
            status=ObservedStatusEnum.ACTIVE,
            last_camera_id=camera_id,
            best_recognition_face_id=face_id,
            best_face_image_url=image_url,
            times_seen=1
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
            db.commit()
            db.refresh(observed)
        return observed

    def create_observed_embedding(self, db: Session, observed_id: int, face_id: int, result: EngineResultContract) -> ObservedIdentityEmbeddingModel:
        """Guarda un nuevo embedding para una identidad observada."""
        emb = ObservedIdentityEmbeddingModel(
            observed_identity_id=observed_id,
            recognition_face_id=face_id,
            engine=result.engine,
            model_name=result.model_name,
            embedding_vector=result.embedding,
            embedding_dim=result.embedding_dim,
            quality_score=result.raw_response.get("det_score") if result.raw_response else None,
            is_representative=True # Por simplificar, el nuevo siempre es representativo o podríamos manejar lógica de máximo
        )
        db.add(emb)
        db.commit()
        db.refresh(emb)
        return emb

recognition_repository = RecognitionRepository()
