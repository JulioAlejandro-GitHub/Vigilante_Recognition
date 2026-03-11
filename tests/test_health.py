import pytest
from unittest.mock import patch, MagicMock
from src.app.health import HealthMonitor
from src.config.settings import settings
import logging

def test_health_monitor_disabled(caplog):
    """Test that the monitor does not run if disabled in settings."""
    settings.enable_healthcheck = False
    monitor = HealthMonitor()

    with caplog.at_level(logging.INFO):
        monitor.run()

    assert "HealthCheck deshabilitado por configuración" in caplog.text

@patch('src.app.health.engine')
@patch('src.app.health.recognition_queue')
@patch('src.app.health.streaming_manager')
def test_health_check_ok(mock_streaming_manager, mock_queue, mock_engine, caplog):
    """Test a successful healthcheck iteration."""
    # Mock DB Connection
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    # Mock Queue Size
    mock_queue.qsize.return_value = 10

    # Mock streaming manager workers (all alive)
    mock_worker1 = MagicMock()
    mock_worker1.is_alive.return_value = True
    mock_streaming_manager.workers = {1: mock_worker1}

    monitor = HealthMonitor()

    with caplog.at_level(logging.INFO):
        monitor._check_health()

    assert "HEALTHCHECK OK: DB=ok, Queue=10, Workers=1" in caplog.text
    assert mock_conn.execute.called

@patch('src.app.health.engine')
@patch('src.app.health.recognition_queue')
@patch('src.app.health.streaming_manager')
def test_health_check_degraded(mock_streaming_manager, mock_queue, mock_engine, caplog):
    """Test a degraded healthcheck (dead worker and db error)."""
    from sqlalchemy.exc import SQLAlchemyError

    # Mock DB Connection error
    mock_engine.connect.side_effect = SQLAlchemyError("Connection refused")

    # Mock Queue Size warning
    mock_queue.qsize.return_value = 600

    # Mock dead worker
    mock_worker1 = MagicMock()
    mock_worker1.is_alive.return_value = False
    mock_streaming_manager.workers = {2: mock_worker1}

    monitor = HealthMonitor()

    with caplog.at_level(logging.WARNING):
        monitor._check_health()

    assert "HEALTHCHECK FALLÓ: Sin conexión a base de datos" in caplog.text
    assert "Cola de reconocimiento alta" in caplog.text
    assert "Worker de cámara 2 ha muerto" in caplog.text
    assert "HEALTHCHECK DEGRADED" in caplog.text
