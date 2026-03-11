import pytest
import logging
from src.utils.logger import StructuredFormatter, ContextLogger

def test_structured_formatter_no_context():
    """Test the formatter output when there is no context injected."""
    formatter = StructuredFormatter()
    record = logging.LogRecord("test_logger", logging.INFO, "test.py", 10, "Mensaje de prueba", (), None)

    formatted_msg = formatter.format(record)
    assert "Mensaje de prueba" in formatted_msg
    assert "Context:" not in formatted_msg

def test_structured_formatter_with_context():
    """Test the formatter output when custom context like camera_id is present."""
    formatter = StructuredFormatter()
    record = logging.LogRecord("test_logger", logging.INFO, "test.py", 10, "Mensaje de prueba", (), None)
    record.camera_id = 99
    record.job_id = "abc-123"

    formatted_msg = formatter.format(record)
    assert "Mensaje de prueba" in formatted_msg
    assert "Context: " in formatted_msg
    assert '"camera_id": 99' in formatted_msg
    assert '"job_id": "abc-123"' in formatted_msg

def test_context_logger_injection():
    """Test that ContextLogger correctly passes its extra attributes to records."""
    import io
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(StructuredFormatter())

    logger = logging.getLogger("test_context")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Wrap it
    context_logger = ContextLogger(logger, {"camera_id": 42})
    context_logger.info("Testeando Inyeccion")

    output = log_capture.getvalue()
    assert "Testeando Inyeccion" in output
    assert '"camera_id": 42' in output

    # Check that ContextLogger does not alter standard loggers
    logger.info("Sin contexto")
    output = log_capture.getvalue()
    assert "Sin contexto" in output.split("\n")[1]
    assert "Context:" not in output.split("\n")[1]
