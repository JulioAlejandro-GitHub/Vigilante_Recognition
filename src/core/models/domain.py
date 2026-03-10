from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class CameraConfig:
    """Configuración de una cámara extraída de la BD"""
    id: int
    nombre: str
    url_stream: str
    activa: bool
    fps_procesamiento: int

@dataclass
class RecognitionJob:
    """Trabajo de reconocimiento enviado a la cola"""
    camera_id: int
    source_type: str
    source_ref: str
    timestamp: datetime
    frame_data: Optional[bytes] = None  # Frame codificado (ej. JPEG) o referencia de ruta
    metadata: Optional[Dict[str, Any]] = None
    tracking_id: Optional[str] = None

@dataclass
class EngineResult:
    """Resultado del motor de reconocimiento (InsightFace, DeepFace, etc)"""
    engine_name: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    embedding: Optional[List[float]] = None
    matched_person_id: Optional[int] = None
    processing_time_ms: float = 0.0

@dataclass
class RecognitionEventData:
    """Datos agregados de un evento de reconocimiento para su persistencia"""
    camera_id: int
    timestamp: datetime
    results: List[EngineResult]
    original_frame_path: Optional[str] = None
