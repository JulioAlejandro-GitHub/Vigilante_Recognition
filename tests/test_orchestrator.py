import pytest
from unittest.mock import MagicMock, patch
from src.recognition_orchestrator.orchestrator import RecognitionOrchestrator
from src.core.models.domain import RecognitionJob
from datetime import datetime

@patch("src.recognition_orchestrator.orchestrator.SessionLocal")
@patch("src.recognition_orchestrator.orchestrator.camera_repository")
def test_orchestrator_process_job_db_error_rollback(mock_camera_repo, mock_session_local):
    """
    Test que verifica que si ocurre un error en la BD durante el procesamiento de un job,
    se llama a db.rollback() y la excepción es propagada o logueada correctamente.
    """
    # Configurar el mock de la sesión de base de datos
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Simular que encontramos una cámara
    mock_camera_repo.get.return_value = MagicMock(local_id=1)

    # Crear un mock del orquestador (no necesitamos inicializar motores para esta prueba
    # si mockeamos la función _process_job interna, pero aquí estamos probando _process_job)
    # Por lo tanto, mockearemos los servicios y repositorios.

    # Crear un orquestador dummy sin arrancar el hilo
    mock_queue = MagicMock()
    orchestrator = RecognitionOrchestrator(mock_queue)

    # Crear un job de prueba
    job = RecognitionJob(
        camera_id=1,
        source_type="test",
        source_ref="test",
        frame_data=None,
        timestamp=datetime.utcnow(),
        metadata={}
    )

    # Simular un error en repository operations
    with patch("src.recognition_orchestrator.orchestrator.recognition_repository") as mock_rec_repo:
        mock_rec_repo.create_solicitud.side_effect = Exception("Simulated DB error")

        with pytest.raises(Exception) as excinfo:
            orchestrator._process_job(job, {"camera_id": 1, "job_id": "job_123"})

        assert "Simulated DB error" in str(excinfo.value)

        # Verificar que se llamó a db.rollback() y db.close()
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()
        # Verificar que NO se llamó a db.commit()
        mock_db.commit.assert_not_called()
