import logging
import sys
import json
from src.config.settings import settings

class StructuredFormatter(logging.Formatter):
    """
    Formatter for structured logging. Includes custom fields like camera_id and job_id
    if they are present in the log record's __dict__ (e.g., passed via `extra`).
    """
    def format(self, record):
        # Base format as required
        log_format = f"{self.formatTime(record, self.datefmt)} - [{record.levelname}] - {record.name} - {record.getMessage()}"

        # Add context fields if present
        context = {}
        if hasattr(record, 'camera_id'):
            context['camera_id'] = record.camera_id
        if hasattr(record, 'job_id'):
            context['job_id'] = record.job_id

        if context:
            log_format += f" | Context: {json.dumps(context)}"

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            log_format += f"\n{record.exc_text}"

        return log_format

def setup_logging():
    """
    Configura el sistema de logging centralizado para la aplicación.
    Utiliza el LOG_LEVEL definido en la configuración (settings).
    """
    log_level_str = settings.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    # We use root logger config, but clear existing handlers first to avoid duplicates
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers if setup_logging is called multiple times
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)

class ContextLogger(logging.LoggerAdapter):
    """
    A LoggerAdapter to easily inject context (like camera_id) into log records.
    """
    def process(self, msg, kwargs):
        kwargs["extra"] = self.extra
        return msg, kwargs

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para un módulo específico.

    Args:
        name: El nombre del módulo (típicamente __name__)

    Returns:
        Instancia de logging.Logger
    """
    return logging.getLogger(name)
