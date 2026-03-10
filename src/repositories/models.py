from sqlalchemy import Column, Integer, String, Boolean, DateTime, SmallInteger, Enum, BigInteger, JSON, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from src.db.session import Base

class SolicitudRecognitionModel(Base):
    __tablename__ = "solicitud_recognition"

    id_solicitud = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("camara.camara_id"), nullable=True)
    source_type = Column(Enum('camera', 'video_file', 'dvr', 'upload', 'api'), nullable=False, default='camera')
    source_ref = Column(String(500), nullable=True)
    img = Column(String(255), nullable=True)
    sharp_ok = Column(Boolean, nullable=True)
    status = Column(Enum('pendiente', 'procesando', 'procesada', 'error'), nullable=False, default='pendiente')
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    events = relationship("RecognitionEventModel", back_populates="solicitud")

class RecognitionEventModel(Base):
    __tablename__ = "recognition_event"

    recognition_event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    id_solicitud = Column(BigInteger, ForeignKey("solicitud_recognition.id_solicitud"), nullable=True)
    camara_id = Column(Integer, ForeignKey("camara.camara_id"), nullable=False)
    local_id = Column(Integer, nullable=False)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    frame_img = Column(String(255), nullable=True)
    frame_metadata = Column(JSON, nullable=True)
    source_type = Column(Enum('camera', 'video_file', 'dvr', 'upload', 'api'), nullable=False, default='camera')
    processing_status = Column(Enum('ok', 'sin_rostro', 'error'), nullable=False, default='ok')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    solicitud = relationship("SolicitudRecognitionModel", back_populates="events")
    faces = relationship("RecognitionFaceModel", back_populates="event")

class RecognitionFaceModel(Base):
    __tablename__ = "recognition_face"

    recognition_face_id = Column(BigInteger, primary_key=True, autoincrement=True)
    recognition_event_id = Column(BigInteger, ForeignKey("recognition_event.recognition_event_id"), nullable=False)
    face_index = Column(SmallInteger, nullable=False, default=1)
    face_img = Column(String(255), nullable=True)
    box = Column(JSON, nullable=True)
    perfil = Column(Enum('front', 'left', 'right', 'top', 'undetected'), nullable=False, default='undetected')
    quality_score = Column(Numeric(10, 6), nullable=True)
    human_score = Column(Numeric(10, 6), nullable=True)
    final_label = Column(Enum('desconocido', 'identificado', 'ladron', 'rechazado', 'revisar'), nullable=False, default='desconocido')
    estado_validacion = Column(Enum('valido', 'por_validar', 'invalido'), nullable=False, default='por_validar')
    assigned_persona_id = Column(BigInteger, nullable=True)
    assigned_status = Column(Enum('sin_asignar', 'auto_asignado', 'manual_asignado', 'enrolado_desde_evento'), nullable=False, default='sin_asignar')
    best_similarity = Column(Numeric(10, 8), nullable=True)
    best_engine = Column(Enum('human', 'insightface', 'deepface', 'facenet', 'arcface', 'otro'), nullable=True)
    reviewed_by_operador_id = Column(Integer, nullable=True)

    event = relationship("RecognitionEventModel", back_populates="faces")
