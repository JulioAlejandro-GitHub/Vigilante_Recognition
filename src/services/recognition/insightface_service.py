import time
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from typing import Any, Dict, List, Optional
from src.services.recognition.interface import RecognitionEngineInterface, EngineResultContract
from src.utils.logger import get_logger

logger = get_logger(__name__)

class InsightFaceService(RecognitionEngineInterface):
    def __init__(self, model_name: str = 'buffalo_l', threshold: float = 0.5):
        self.model_name = model_name
        self.threshold = threshold
        self.app = None

    def initialize(self) -> None:
        """Inicializa InsightFace (detección y reconocimiento)"""
        logger.info(f"Inicializando InsightFace con modelo {self.model_name}")
        self.app = FaceAnalysis(name=self.model_name, providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("InsightFace inicializado correctamente")

    def _cosine_similarity(self, embed1: np.ndarray, embed2: np.ndarray) -> float:
        """Calcula la similitud coseno entre dos embeddings"""
        return np.dot(embed1, embed2) / (np.linalg.norm(embed1) * np.linalg.norm(embed2))

    def process_face(self, face_img: Any, gallery: List[Dict[str, Any]]) -> EngineResultContract:
        start_time = time.time()

        # 1. Detección y extracción de embedding
        faces = self.app.get(face_img)

        if not faces:
            logger.debug("InsightFace no detectó ningún rostro en la imagen proporcionada.")
            return EngineResultContract(
                engine="insightface",
                model_name=self.model_name,
                detected_human=False,
                processing_ms=int((time.time() - start_time) * 1000)
            )

        # Tomar el rostro con mayor score
        best_face = max(faces, key=lambda f: f.det_score)
        embedding = best_face.normed_embedding

        # 2. Matching contra galería (combinada: conocidos y observados)
        best_match_id = None
        best_embedding_id = None
        best_observed_id = None
        best_observed_embedding_id = None

        best_similarity_persona = -1.0
        best_similarity_observed = -1.0

        for item in gallery:
            # Filtrar por engine para evitar dimension mismatch con otros motores
            if item.get('engine') != 'insightface':
                continue

            gal_embed = np.array(item['embedding'], dtype=np.float32)
            similarity = self._cosine_similarity(embedding, gal_embed)

            if 'persona_id' in item and item['persona_id'] is not None:
                if similarity > best_similarity_persona:
                    best_similarity_persona = similarity
                    best_match_id = item['persona_id']
                    best_embedding_id = item.get('persona_embedding_id')
            elif 'observed_identity_id' in item and item['observed_identity_id'] is not None:
                if similarity > best_similarity_observed:
                    best_similarity_observed = similarity
                    best_observed_id = item['observed_identity_id']
                    best_observed_embedding_id = item.get('observed_identity_embedding_id')

        # Escoger la similitud máxima global para la respuesta
        max_similarity = max(best_similarity_persona, best_similarity_observed)

        return EngineResultContract(
            engine="insightface",
            model_name=self.model_name,
            model_version="latest",
            detected_human=True,
            similarity=float(max_similarity) if max_similarity != -1.0 else None,
            candidate_persona_id=best_match_id,
            candidate_persona_embedding_id=best_embedding_id,
            candidate_observed_id=best_observed_id,
            candidate_observed_embedding_id=best_observed_embedding_id,
            embedding=embedding.tolist(),
            embedding_dim=len(embedding),
            processing_ms=int((time.time() - start_time) * 1000),
            raw_response={"det_score": float(best_face.det_score), "bbox": best_face.bbox.tolist(),
                          "sim_persona": float(best_similarity_persona), "sim_observed": float(best_similarity_observed)}
        )

# Instancia global para ser usada por el orquestador
insightface_service = InsightFaceService()
