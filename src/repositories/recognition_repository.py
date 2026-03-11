from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from src.repositories.base import BaseRepository
from src.repositories.models import SolicitudRecognitionModel, RecognitionEventModel, RecognitionFaceModel, PersonaEmbeddingModel, RecognitionEngineResultModel
from src.core.models.domain import RecognitionJob
from src.services.recognition.interface import EngineResultContract
from src.core.enums.domain import SolicitudStatusEnum, EstadoEnum, FinalLabelEnum, ProcessingStatusEnum

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

    def create_event(self, db: Session, solicitud_id: int, camera_id: int, local_id: int, job: RecognitionJob, frame_img: Optional[str] = None, processing_status: str = ProcessingStatusEnum.OK) -> RecognitionEventModel:
        """Crea un nuevo evento de reconocimiento asociado a una solicitud"""
        event = RecognitionEventModel(
            id_solicitud=solicitud_id,
            camara_id=camera_id,
            local_id=local_id,
            occurred_at=job.timestamp,
            frame_img=frame_img,
            frame_metadata=job.metadata,
            source_type=job.source_type,
            processing_status=processing_status
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def create_face(self, db: Session, event_id: int, face_index: int = 1, box: Optional[Dict] = None) -> RecognitionFaceModel:
        """Crea un registro de rostro detectado para un evento"""
        face = RecognitionFaceModel(
            recognition_event_id=event_id,
            face_index=face_index,
            box=box
        )
        db.add(face)
        db.commit()
        db.refresh(face)
        return face

    def get_persona_embeddings(self, db: Session) -> List[Dict[str, Any]]:
        """Obtiene la galería de embeddings de personas activas."""
        embeddings = db.query(PersonaEmbeddingModel).filter(
            PersonaEmbeddingModel.estado == EstadoEnum.ACTIVO
        ).all()

        gallery = []
        for emb in embeddings:
            gallery.append({
                "persona_id": emb.persona_id,
                "persona_embedding_id": emb.persona_embedding_id,
                "engine": emb.engine,
                "embedding": emb.embedding
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

    def update_face_with_best_match(self, db: Session, face_id: int, result: EngineResultContract) -> None:
        """Actualiza el registro del rostro con la decisión final del orquestador."""
        face = db.query(RecognitionFaceModel).filter(RecognitionFaceModel.recognition_face_id == face_id).first()
        if face and result.candidate_persona_id:
            face.assigned_persona_id = result.candidate_persona_id
            face.best_similarity = result.similarity
            face.best_engine = result.engine
            face.final_label = FinalLabelEnum.IDENTIFICADO
            db.commit()

recognition_repository = RecognitionRepository()
