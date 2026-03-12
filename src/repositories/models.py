from sqlalchemy import Column, Integer, String, Boolean, DateTime, SmallInteger, Enum as SQLEnum, BigInteger, JSON, ForeignKey, Numeric, Text
from src.core.enums.domain import (
    SourceTypeEnum, SolicitudStatusEnum, ProcessingStatusEnum, PerfilEnum,
    FinalLabelEnum, EstadoValidacionEnum, AssignedStatusEnum, EngineEnum,
    PersonaTipoEnum, EstadoEnum, ObservedStatusEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
from src.db.session import Base

class SolicitudRecognitionModel(Base):
    __tablename__ = "solicitud_recognition"

    id_solicitud = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("camara.camara_id"), nullable=True)
    source_type = Column(SQLEnum(SourceTypeEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=SourceTypeEnum.CAMERA)
    source_ref = Column(String(500), nullable=True)
    img = Column(String(255), nullable=True)
    sharp_ok = Column(Boolean, nullable=True)
    status = Column(SQLEnum(SolicitudStatusEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=SolicitudStatusEnum.PENDIENTE)
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
    frame_image_url = Column(String(1024), nullable=True)
    frame_metadata = Column(JSON, nullable=True)
    source_type = Column(SQLEnum(SourceTypeEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=SourceTypeEnum.CAMERA)
    processing_status = Column(SQLEnum(ProcessingStatusEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=ProcessingStatusEnum.OK)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    solicitud = relationship("SolicitudRecognitionModel", back_populates="events")
    faces = relationship("RecognitionFaceModel", back_populates="event")

class RecognitionFaceModel(Base):
    __tablename__ = "recognition_face"

    recognition_face_id = Column(BigInteger, primary_key=True, autoincrement=True)
    recognition_event_id = Column(BigInteger, ForeignKey("recognition_event.recognition_event_id"), nullable=False)
    face_index = Column(SmallInteger, nullable=False, default=1)
    face_img = Column(String(255), nullable=True)
    face_preview_img = Column(String(255), nullable=True)
    face_image_url = Column(String(1024), nullable=True)
    face_preview_url = Column(String(1024), nullable=True)
    box = Column(JSON, nullable=True)
    perfil = Column(SQLEnum(PerfilEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=PerfilEnum.UNDETECTED)
    quality_score = Column(Numeric(10, 6), nullable=True)
    human_score = Column(Numeric(10, 6), nullable=True)
    final_label = Column(SQLEnum(FinalLabelEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=FinalLabelEnum.DESCONOCIDO)
    estado_validacion = Column(SQLEnum(EstadoValidacionEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=EstadoValidacionEnum.POR_VALIDAR)
    assigned_persona_id = Column(BigInteger, nullable=True)
    assigned_status = Column(SQLEnum(AssignedStatusEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=AssignedStatusEnum.SIN_ASIGNAR)
    best_similarity = Column(Numeric(10, 8), nullable=True)
    best_engine = Column(SQLEnum(EngineEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=True)
    observed_identity_id = Column(BigInteger, ForeignKey("observed_identity.observed_identity_id"), nullable=True)
    reviewed_by_operador_id = Column(Integer, nullable=True)

    event = relationship("RecognitionEventModel", back_populates="faces")
    observed_identity = relationship("ObservedIdentityModel", back_populates="faces", foreign_keys=[observed_identity_id])

class ObservedIdentityModel(Base):
    __tablename__ = "observed_identity"

    observed_identity_id = Column(BigInteger, primary_key=True, autoincrement=True)
    status = Column(SQLEnum(ObservedStatusEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=ObservedStatusEnum.ACTIVE)
    display_label = Column(String(150), nullable=True)
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    times_seen = Column(Integer, nullable=False, default=1)
    last_camera_id = Column(Integer, ForeignKey("camara.camara_id"), nullable=True)
    best_recognition_face_id = Column(BigInteger, ForeignKey("recognition_face.recognition_face_id"), nullable=True)
    best_face_image_url = Column(String(1024), nullable=True)
    notes = Column(Text, nullable=True)
    promoted_persona_id = Column(BigInteger, ForeignKey("persona.persona_id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    faces = relationship("RecognitionFaceModel", back_populates="observed_identity", foreign_keys="[RecognitionFaceModel.observed_identity_id]")
    embeddings = relationship("ObservedIdentityEmbeddingModel", back_populates="observed_identity")

class ObservedIdentityEmbeddingModel(Base):
    __tablename__ = "observed_identity_embedding"

    observed_identity_embedding_id = Column(BigInteger, primary_key=True, autoincrement=True)
    observed_identity_id = Column(BigInteger, ForeignKey("observed_identity.observed_identity_id"), nullable=False)
    recognition_face_id = Column(BigInteger, ForeignKey("recognition_face.recognition_face_id"), nullable=False)
    engine = Column(SQLEnum(EngineEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    model_name = Column(String(100), nullable=True)
    embedding_vector = Column(JSON, nullable=False)
    embedding_dim = Column(SmallInteger, nullable=True)
    quality_score = Column(Numeric(10, 6), nullable=True)
    is_representative = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    observed_identity = relationship("ObservedIdentityModel", back_populates="embeddings")

class PersonaModel(Base):
    __tablename__ = "persona"

    persona_id = Column(BigInteger, primary_key=True, autoincrement=True)
    local_id = Column(Integer, nullable=False)
    codigo_externo = Column(String(100), nullable=True)
    nombre = Column(String(150), nullable=False)
    tipo = Column(SQLEnum(PersonaTipoEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=PersonaTipoEnum.OTRO)
    estado = Column(SQLEnum(EstadoEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=EstadoEnum.ACTIVO)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)

    embeddings = relationship("PersonaEmbeddingModel", back_populates="persona")

class PersonaEmbeddingModel(Base):
    __tablename__ = "persona_embedding"

    persona_embedding_id = Column(BigInteger, primary_key=True, autoincrement=True)
    persona_id = Column(BigInteger, ForeignKey("persona.persona_id"), nullable=False)
    engine = Column(SQLEnum(EngineEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    embedding_dim = Column(SmallInteger, nullable=True)
    embedding = Column(JSON, nullable=False)
    embedding_hash = Column(String(64), nullable=True)
    img_origen = Column(String(255), nullable=True)
    face_box = Column(JSON, nullable=True)
    perfil = Column(SQLEnum(PerfilEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=PerfilEnum.UNDETECTED)
    quality_score = Column(Numeric(10, 6), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    estado = Column(SQLEnum(EstadoEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=EstadoEnum.ACTIVO)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    persona = relationship("PersonaModel", back_populates="embeddings")

class RecognitionEngineResultModel(Base):
    __tablename__ = "recognition_engine_result"

    recognition_engine_result_id = Column(BigInteger, primary_key=True, autoincrement=True)
    recognition_face_id = Column(BigInteger, ForeignKey("recognition_face.recognition_face_id"), nullable=False)
    engine = Column(SQLEnum(EngineEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    detected_human = Column(Boolean, nullable=True)
    similarity = Column(Numeric(10, 8), nullable=True)
    candidate_persona_id = Column(BigInteger, ForeignKey("persona.persona_id"), nullable=True)
    candidate_persona_embedding_id = Column(BigInteger, ForeignKey("persona_embedding.persona_embedding_id"), nullable=True)
    img = Column(String(255), nullable=True)
    box = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)
    embedding_dim = Column(SmallInteger, nullable=True)
    embedding_hash = Column(String(64), nullable=True)
    processing_ms = Column(Integer, nullable=True)
    raw_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
