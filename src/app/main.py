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

    # Arrancar fase 2: Streaming e Ingesta YOLO
    start_streaming_service()

    return True

def start_streaming_service():
    """
    Arranca los servicios RTSP, detector temprano YOLO y el orquestador de reconocimiento.
    Lee cámaras directamente de BD.
    """
    from src.services.cam_streaming.manager import streaming_manager
    from src.recognition_orchestrator.orchestrator import orchestrator
    from src.app.health import health_monitor
    from src.utils.logger import get_logger
    import time

    logger = get_logger(__name__)
    logger.info(">>> Iniciando Módulo Streaming, Detección YOLO y Orquestador de Reconocimiento <<<")

    try:
        # Arrancar el monitor de salud (background thread)
        if settings.enable_healthcheck:
            health_monitor.start()
        else:
            logger.info("HealthCheck Monitor está deshabilitado por configuración.")

        # Arrancar orquestador de reconocimiento (background thread)
        orchestrator.start()

        # Arrancar streaming de cámaras y workers de detección
        streaming_manager.start_streaming()

        # Keep main thread alive as workers run in background threads
        logger.info("Aplicación corriendo... Presione Ctrl+C para salir.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Recibida señal de detención. Apagando workers...")
        health_monitor.stop()
        streaming_manager.stop_all()
        orchestrator.stop()

        health_monitor.join(timeout=3)
        orchestrator.join(timeout=3)

if __name__ == "__main__":
    bootstrap()
