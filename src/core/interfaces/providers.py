from abc import ABC, abstractmethod
from typing import Iterator, Any
from src.core.models.domain import RecognitionJob, EngineResult, RecognitionEventData

class StreamProvider(ABC):
    """Interfaz para proveedores de streaming de video"""

    @abstractmethod
    def start(self) -> None:
        """Inicia el streaming"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Detiene el streaming"""
        pass

    @abstractmethod
    def read_frames(self) -> Iterator[Any]:
        """Devuelve un iterador de frames"""
        pass

class RecognitionQueue(ABC):
    """Interfaz para cola de trabajos de reconocimiento"""

    @abstractmethod
    def enqueue(self, job: RecognitionJob) -> bool:
        """Añade un trabajo a la cola"""
        pass

    @abstractmethod
    def dequeue(self) -> RecognitionJob:
        """Extrae un trabajo de la cola"""
        pass

class RecognitionEngine(ABC):
    """Interfaz para motores de reconocimiento (InsightFace, DeepFace)"""

    @abstractmethod
    def initialize(self) -> None:
        """Inicializa los modelos del motor"""
        pass

    @abstractmethod
    def process_frame(self, frame: Any) -> list[EngineResult]:
        """Procesa un frame y devuelve resultados de reconocimiento"""
        pass

class EventWriter(ABC):
    """Interfaz para guardar eventos de reconocimiento (BD, Mensajería, etc)"""

    @abstractmethod
    def save_event(self, event_data: RecognitionEventData) -> bool:
        """Guarda un evento de reconocimiento"""
        pass
