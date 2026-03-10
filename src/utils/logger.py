import logging
import sys
from src.config.settings import settings

def setup_logging():
    """
    Configura el sistema de logging centralizado para la aplicación.
    Utiliza el LOG_LEVEL definido en la configuración (settings).
    """
    log_level_str = settings.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    log_format = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para un módulo específico.

    Args:
        name: El nombre del módulo (típicamente __name__)

    Returns:
        Instancia de logging.Logger
    """
    return logging.getLogger(name)
