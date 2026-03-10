from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from src.repositories.base import BaseRepository
from src.repositories.models import SolicitudRecognitionModel, RecognitionEventModel, RecognitionFaceModel
from src.core.models.domain import RecognitionJob

class RecognitionRepository:
    """Repositorio para gestionar solicitudes y eventos de reconocimiento en BD"""

    def create_solicitud(self, db: Session, job: RecognitionJob, img_path: Optional[str] = None) -> SolicitudRecognitionModel:
        """Crea una nueva solicitud de reconocimiento"""
        solicitud = SolicitudRecognitionModel(
            camera_id=job.camera_id,
            source_type=job.source_type,
            source_ref=job.source_ref,
            img=img_path,
            status='procesando',
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
            if status in ['procesada', 'error']:
                solicitud.processed_at = datetime.utcnow()
            db.commit()
            db.refresh(solicitud)
        return solicitud

    def create_event(self, db: Session, solicitud_id: int, camera_id: int, local_id: int, job: RecognitionJob, frame_img: Optional[str] = None, processing_status: str = 'ok') -> RecognitionEventModel:
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

recognition_repository = RecognitionRepository()
