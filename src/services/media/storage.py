import cv2
import numpy as np
from datetime import datetime
from src.utils.logger import get_logger
from src.services.media.storage_client import storage_client

logger = get_logger(__name__)

class StorageService:
    def __init__(self):
        pass

    def _encode_image(self, img_array: np.ndarray) -> bytes:
        """Codifica un array numpy como imagen JPEG en memoria."""
        if img_array is None or img_array.size == 0:
            logger.error("Intento de codificar imagen vacía")
            return None

        try:
            success, buffer = cv2.imencode(".jpg", img_array)
            if not success:
                logger.error("Error cv2.imencode codificando imagen")
                return None
            return buffer.tobytes()
        except Exception as e:
            logger.error(f"Excepción codificando imagen: {e}")
            return None

    def save_frame_full(self, camera_id: int, event_id: int, timestamp: datetime, frame_img: np.ndarray) -> tuple[str, str]:
        """
        Sube la imagen completa del frame original al Storage Service.
        Retorna (object_key, public_url) o (None, None) si falla.
        """
        img_bytes = self._encode_image(frame_img)
        if not img_bytes:
            return None, None

        response = storage_client.upload_image(
            image_bytes=img_bytes,
            image_kind="frame_full",
            filename="frame_full.jpg",
            camera_id=camera_id,
            recognition_event_id=event_id
        )

        if response and response.get("public_url"):
            public_url = response.get("public_url")
            object_key = response.get("object_key", "")
            logger.info(f"Subido frame_full: {public_url}")
            return object_key, public_url

        return None, None

    def save_face_crop(self, camera_id: int, event_id: int, face_index: int, timestamp: datetime, face_img: np.ndarray) -> tuple[str, str]:
        """
        Sube el recorte del rostro al Storage Service.
        Retorna (object_key, public_url) o (None, None) si falla.
        """
        img_bytes = self._encode_image(face_img)
        if not img_bytes:
            return None, None

        response = storage_client.upload_image(
            image_bytes=img_bytes,
            image_kind="face_crop",
            filename=f"face_{face_index}.jpg",
            camera_id=camera_id,
            recognition_event_id=event_id,
            face_index=face_index
        )

        if response and response.get("public_url"):
            public_url = response.get("public_url")
            object_key = response.get("object_key", "")
            logger.info(f"Subido face_crop {face_index}: {public_url}")
            return object_key, public_url

        return None, None

    def save_face_preview(self, camera_id: int, event_id: int, face_index: int, timestamp: datetime, face_img: np.ndarray, max_size: int = 150) -> tuple[str, str]:
        """
        Sube una versión ligera del recorte del rostro para UX al Storage Service.
        Retorna (object_key, public_url) o (None, None) si falla.
        """
        if face_img is None or face_img.size == 0:
            return None, None

        # Redimensionar manteniendo el ratio si es más grande que max_size
        h, w = face_img.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            preview_img = cv2.resize(face_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            preview_img = face_img

        img_bytes = self._encode_image(preview_img)
        if not img_bytes:
            return None, None

        response = storage_client.upload_image(
            image_bytes=img_bytes,
            image_kind="face_preview",
            filename=f"face_{face_index}_preview.jpg",
            camera_id=camera_id,
            recognition_event_id=event_id,
            face_index=face_index
        )

        if response and response.get("public_url"):
            public_url = response.get("public_url")
            object_key = response.get("object_key", "")
            logger.info(f"Subido face_preview {face_index}: {public_url}")
            return object_key, public_url

        return None, None

storage_service = StorageService()
