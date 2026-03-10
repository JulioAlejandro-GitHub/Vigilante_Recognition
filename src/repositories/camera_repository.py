from typing import List
from src.repositories.base import BaseRepository
from src.db.session import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, SmallInteger, Enum
from sqlalchemy.orm import Session
from datetime import datetime

class CamaraModel(Base):
    """Modelo ORM para la tabla camara"""
    __tablename__ = "camara"

    camara_id = Column(Integer, primary_key=True, index=True)
    local_id = Column(Integer, nullable=False)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(Enum('Ingreso','Estadia','Salida','Otro'), default='Estadia', nullable=False)
    estado = Column(Enum('Activo','Inactivo'), default='Activo', nullable=False)
    orden = Column(Integer, default=None)
    protocolo = Column(Enum('onvif','webcam','rtsp','archivo','dvr'), default='onvif', nullable=False)
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

    def get_active_cameras(self, db: Session) -> List[CamaraModel]:
        """Obtiene todas las cámaras que están en estado 'Activo'"""
        return db.query(self.model).filter(self.model.estado == 'Activo').all()

camera_repository = CamaraRepository()
