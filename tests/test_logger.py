import logging
from io import StringIO
from src.utils.logger import StructuredFormatter

def test_structured_formatter_with_extra():
    formatter = StructuredFormatter("%(message)s")

    # Create a record with extra fields
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.camera_id = 123
    record.job_id = "job_1"

    formatted_msg = formatter.format(record)
    assert "[cam:123][job:job_1] Test message" == formatted_msg

def test_structured_formatter_without_extra():
    formatter = StructuredFormatter("%(message)s")

    # Create a record without extra fields
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )

    formatted_msg = formatter.format(record)
    assert "Test message" == formatted_msg
