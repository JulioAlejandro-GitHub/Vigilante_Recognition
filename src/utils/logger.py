import logging
import sys
from src.config.settings import settings

class StructuredFormatter(logging.Formatter):
    """
    Formateador personalizado para soportar metadatos adicionales en los logs.
    Permite inyectar variables como `camera_id`, `job_id`, etc., si están en los kwargs de extra.
    """
    def format(self, record):
        # Asegurarse de que los campos existan en el record, si no, ponerlos vacíos
        record.camera_info = f"[cam:{record.camera_id}]" if hasattr(record, 'camera_id') else ""
        record.job_info = f"[job:{record.job_id}]" if hasattr(record, 'job_id') else ""

        # Juntar la info extra si existe
        extra_info = f"{record.camera_info}{record.job_info}"
        if extra_info:
            extra_info += " "

        # Reemplazar el mensaje con la info extra
        original_msg = record.msg
        record.msg = f"{extra_info}{original_msg}"

        result = super().format(record)

        # Restaurar el mensaje original por si otros handlers lo necesitan
        record.msg = original_msg

        return result

def setup_logging():
    """
    Configura el sistema de logging centralizado para la aplicación.
    Utiliza el LOG_LEVEL definido en la configuración (settings).
    """
    log_level_str = settings.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Limpiar handlers previos para evitar duplicados en reinicios
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    log_format = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
    formatter = StructuredFormatter(log_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para un módulo específico.

    Args:
        name: El nombre del módulo (típicamente __name__)

    Returns:
        Instancia de logging.Logger
    """
    return logging.getLogger(name)
