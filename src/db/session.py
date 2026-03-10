from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.settings import settings

# Engine global
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Para comprobar si la conexión sigue viva
    echo=False          # Cambiar a True para ver queries SQL en logs de nivel DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependencia para inyección de sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
