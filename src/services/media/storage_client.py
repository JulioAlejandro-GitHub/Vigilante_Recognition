import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class StorageClient:
    """Cliente HTTP para comunicarse con el API de Vigilante_Storage"""

    def __init__(self):
        self.base_url = settings.storage_service_base_url.rstrip("/")
        self.upload_endpoint = f"{self.base_url}/api/v1/upload"
        self.timeout = settings.storage_upload_timeout_seconds
        self.enabled = settings.storage_enabled
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Crea una sesión HTTP con política de reintentos."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,  # Número máximo de reintentos
            backoff_factor=0.5,  # Factor de espera (0.5s, 1s, 2s)
            status_forcelist=[429, 500, 502, 503, 504],  # Códigos de error para reintentar
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def upload_image(self,
                     image_bytes: bytes,
                     image_kind: str,
                     filename: str,
                     source_service: Optional[str] = None,
                     camera_id: Optional[int] = None,
                     recognition_event_id: Optional[int] = None,
                     recognition_face_id: Optional[int] = None,
                     face_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Sube una imagen (bytes) vía multipart/form-data al Storage Service.
        """
        if not self.enabled:
            logger.warning("Storage HTTP Client está deshabilitado por configuración. No se subirá la imagen.")
            return None

        source = source_service or settings.storage_source_service

        # Armar la metadata a enviar en el body
        data = {
            "source_service": source,
            "image_kind": image_kind
        }

        # Agregar campos opcionales si vienen
        if camera_id is not None:
            data["camera_id"] = str(camera_id)
        if recognition_event_id is not None:
            data["recognition_event_id"] = str(recognition_event_id)
        if recognition_face_id is not None:
            data["recognition_face_id"] = str(recognition_face_id)
        if face_index is not None:
            data["face_index"] = str(face_index)

        # Preparar el archivo (multipart/form-data)
        # El endpoint espera el field 'file'
        files = {
            "file": (filename, image_bytes, "image/jpeg")
        }

        try:
            logger.debug(f"Intentando subir {image_kind} al storage service ({self.upload_endpoint})...")

            response = self.session.post(
                self.upload_endpoint,
                data=data,
                files=files,
                timeout=self.timeout
            )

            response.raise_for_status()  # Lanza excepción para HTTP 4xx o 5xx

            # Asumimos que la respuesta exitosa viene en JSON format según el contrato
            json_response = response.json()

            logger.debug(f"Upload exitoso de {image_kind}. Respuesta: {json_response.get('object_key', '')}")
            return json_response

        except requests.exceptions.Timeout:
            logger.error(f"Timeout al subir {image_kind} hacia {self.upload_endpoint} después de {self.timeout}s.")
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión al subir {image_kind} hacia {self.upload_endpoint}. ¿Está arriba el servicio?")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error {e.response.status_code} subiendo {image_kind}: {e.response.text}")
        except Exception as e:
            logger.error(f"Error inesperado subiendo {image_kind} al storage: {str(e)}", exc_info=True)

        return None

storage_client = StorageClient()
