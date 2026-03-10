from src.repositories.base import BaseRepository
from src.db.session import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime

class CamaraModel(Base):
    """Modelo ORM para la tabla camara"""
    __tablename__ = "camara"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    ip_url = Column(String(255), nullable=False)
    activa = Column(Boolean, default=True)

class CamaraRepository(BaseRepository[CamaraModel]):
    """Repositorio para operaciones específicas de cámaras"""
    def __init__(self):
        super().__init__(CamaraModel)

camera_repository = CamaraRepository()
