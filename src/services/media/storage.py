import os
import cv2
import numpy as np
from datetime import datetime
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class StorageService:
    def __init__(self):
        self.base_path = settings.storage_base_path
        self.base_url = settings.media_base_url

    def _build_path(self, camera_id: int, event_id: int, dt: datetime, filename: str) -> str:
        """Construye la ruta relativa para un archivo en particular."""
        return f"recognition/cameras/{camera_id}/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/event_{event_id}/{filename}"

    def _get_absolute_path(self, relative_path: str) -> str:
        """Obtiene la ruta absoluta en el sistema de archivos."""
        return os.path.join(self.base_path, relative_path)

    def _get_public_url(self, relative_path: str) -> str:
        """Genera la URL pública para acceder a la imagen."""
        # Se elimina posibles dobles slashes
        return f"{self.base_url.rstrip('/')}/{relative_path}"

    def _ensure_dir(self, file_path: str):
        """Asegura que el directorio exista."""
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)

    def _save_image(self, img_array: np.ndarray, file_path: str) -> bool:
        """Guarda un array numpy como imagen de forma segura."""
        if img_array is None or img_array.size == 0:
            logger.error(f"Intento de guardar imagen vacía en {file_path}")
            return False

        try:
            self._ensure_dir(file_path)
            success = cv2.imwrite(file_path, img_array)
            if not success:
                logger.error(f"Error cv2.imwrite guardando archivo en {file_path}")
                return False
            logger.debug(f"Imagen guardada exitosamente en {file_path}")
            return True
        except Exception as e:
            logger.error(f"Excepción guardando imagen en {file_path}: {e}")
            return False

    def save_frame_full(self, camera_id: int, event_id: int, timestamp: datetime, frame_img: np.ndarray) -> tuple[str, str]:
        """
        Guarda la imagen completa del frame original.
        Retorna (ruta_fisica_relativa, url_publica) o (None, None) si falla.
        """
        rel_path = self._build_path(camera_id, event_id, timestamp, "frame_full.jpg")
        abs_path = self._get_absolute_path(rel_path)

        if self._save_image(frame_img, abs_path):
            public_url = self._get_public_url(rel_path)
            logger.info(f"Guardado frame_full: {public_url}")
            return rel_path, public_url
        return None, None

    def save_face_crop(self, camera_id: int, event_id: int, face_index: int, timestamp: datetime, face_img: np.ndarray) -> tuple[str, str]:
        """
        Guarda el recorte del rostro.
        Retorna (ruta_fisica_relativa, url_publica) o (None, None) si falla.
        """
        rel_path = self._build_path(camera_id, event_id, timestamp, f"face_{face_index}.jpg")
        abs_path = self._get_absolute_path(rel_path)

        if self._save_image(face_img, abs_path):
            public_url = self._get_public_url(rel_path)
            logger.info(f"Guardado face_crop {face_index}: {public_url}")
            return rel_path, public_url
        return None, None

    def save_face_preview(self, camera_id: int, event_id: int, face_index: int, timestamp: datetime, face_img: np.ndarray, max_size: int = 150) -> tuple[str, str]:
        """
        Guarda una versión ligera del recorte del rostro para UX.
        Retorna (ruta_fisica_relativa, url_publica) o (None, None) si falla.
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

        rel_path = self._build_path(camera_id, event_id, timestamp, f"face_{face_index}_preview.jpg")
        abs_path = self._get_absolute_path(rel_path)

        if self._save_image(preview_img, abs_path):
            public_url = self._get_public_url(rel_path)
            logger.info(f"Guardado face_preview {face_index}: {public_url}")
            return rel_path, public_url
        return None, None

storage_service = StorageService()
