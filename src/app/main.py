import sys
import os

# Añade el directorio raíz al PYTHONPATH si se ejecuta el script directamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.exc import SQLAlchemyError
from src.utils.logger import setup_logging, get_logger
from src.config.settings import settings
from src.db.session import engine

def bootstrap():
    """
    Inicializa los componentes base del sistema:
    1. Configuración de Logging
    2. Conexión a la Base de Datos
    """
    setup_logging()
    logger = get_logger(__name__)

    logger.info("Iniciando Vigilante Recognition Architecture Foundation")
    logger.info(f"Nivel de log: {settings.log_level}")
    logger.info(f"Base de datos objetivo: {settings.db_host}:{settings.db_port}/{settings.db_database}")

    try:
        # Intenta una conexión básica para validar configuración
        with engine.connect() as connection:
            logger.info("✅ Conexión a la base de datos MySQL establecida exitosamente.")
            # Un simple query de prueba: connection.execute("SELECT 1") en versiones newer requires text()
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            logger.debug(f"Test query result: {result.fetchone()}")

    except SQLAlchemyError as e:
        logger.error(f"❌ Error crítico conectando a la base de datos: {e}")
        sys.exit(1)

    logger.info("Bootstrap completado. Arquitectura lista para siguientes fases.")
    return True

if __name__ == "__main__":
    bootstrap()
