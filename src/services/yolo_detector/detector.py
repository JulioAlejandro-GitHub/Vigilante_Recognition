import cv2
import numpy as np
import threading
from ultralytics import YOLO
from src.utils.logger import get_logger

logger = get_logger(__name__)

class YOLODetector:
    def __init__(self, model_name: str = "yolov8n.pt", conf_threshold: float = 0.5):
        """
        Inicializa el detector YOLO.
        Por defecto utiliza el modelo nano (yolov8n) que es el más rápido.
        """
        logger.info(f"Cargando modelo YOLO: {model_name}")
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold
        # COCO class 0 es persona. Solo nos interesan las personas.
        self.classes = [0]
        self._lock = threading.Lock()

    def detect(self, frame: np.ndarray):
        """
        Detecta personas en el frame.
        Devuelve una lista de diccionarios con la estructura:
        [{'bbox': [x1, y1, x2, y2], 'conf': float, 'class': int}]
        """
        with self._lock:
            results = self.model.predict(
                source=frame,
                conf=self.conf_threshold,
                classes=self.classes,
                verbose=False # Minimizar ruido en la consola
            )

        detections = []
        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # box.xyxy[0] contiene las coordenadas [x1, y1, x2, y2]
                    # tensor a lista nativa
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = box.conf[0].item()
                    cls_id = int(box.cls[0].item())

                    detections.append({
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "conf": conf,
                        "class": cls_id
                    })

        return detections

    def is_relevant_frame(self, detections: list) -> bool:
        """
        Aplica criterio para seleccionar frames relevantes.
        En esta etapa temprana, un frame es relevante si contiene
        al menos una persona detectada con buena confianza.
        """
        return len(detections) > 0
