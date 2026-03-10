from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class EngineResultContract(BaseModel):
    engine: str
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    detected_human: Optional[bool] = None
    similarity: Optional[float] = None
    candidate_persona_id: Optional[int] = None
    candidate_persona_embedding_id: Optional[int] = None
    embedding: Optional[List[float]] = None
    embedding_dim: Optional[int] = None
    processing_ms: Optional[int] = None
    raw_response: Optional[Dict[str, Any]] = None

class RecognitionEngineInterface(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Inicializa los modelos del motor"""
        pass

    @abstractmethod
    def process_face(self, face_img: Any, gallery: List[Dict[str, Any]]) -> EngineResultContract:
        """Procesa una imagen de rostro recortado, extrae embedding y lo compara con la galería."""
        pass
