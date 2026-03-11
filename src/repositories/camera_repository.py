from typing import List
from src.repositories.base import BaseRepository
from src.db.session import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, SmallInteger, Enum as SQLEnum
from src.core.enums.domain import CamaraUbicacionEnum, CamaraEstadoEnum, CamaraProtocoloEnum
from sqlalchemy.orm import Session
from datetime import datetime

class CamaraModel(Base):
    """Modelo ORM para la tabla camara"""
    __tablename__ = "camara"

    camara_id = Column(Integer, primary_key=True, index=True)
    local_id = Column(Integer, nullable=False)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(SQLEnum(CamaraUbicacionEnum, values_callable=lambda obj: [e.value for e in obj]), default=CamaraUbicacionEnum.ESTADIA, nullable=False)
    estado = Column(SQLEnum(CamaraEstadoEnum, values_callable=lambda obj: [e.value for e in obj]), default=CamaraEstadoEnum.ACTIVO, nullable=False)
    orden = Column(Integer, default=None)
    protocolo = Column(SQLEnum(CamaraProtocoloEnum, values_callable=lambda obj: [e.value for e in obj]), default=CamaraProtocoloEnum.ONVIF, nullable=False)
    camara_hostname = Column(String(100), default=None)
    camara_port = Column(SmallInteger, default=None)
    camara_user = Column(String(100), default=None)
    camara_pass = Column(String(255), default=None)
    camara_params = Column(String(255), default=None)
    stream_url = Column(String(500), default=None)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class CamaraRepository(BaseRepository[CamaraModel]):
    """Repositorio para operaciones específicas de cámaras"""
    def __init__(self):
        super().__init__(CamaraModel)

    def get(self, db: Session, id: int) -> CamaraModel:
        """Obtiene una cámara por su camara_id"""
        return db.query(self.model).filter(self.model.camara_id == id).first()

    def get_active_cameras(self, db: Session) -> List[CamaraModel]:
        """Obtiene todas las cámaras que están en estado 'Activo'"""
        return db.query(self.model).filter(self.model.estado == CamaraEstadoEnum.ACTIVO).all()

camera_repository = CamaraRepository()
