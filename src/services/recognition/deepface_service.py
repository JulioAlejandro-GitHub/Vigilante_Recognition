import time
from typing import Any, Dict, List, Optional
from deepface import DeepFace
from src.services.recognition.interface import RecognitionEngineInterface, EngineResultContract
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DeepFaceService(RecognitionEngineInterface):
    def __init__(self, model_name: str = 'VGG-Face', distance_metric: str = 'cosine'):
        self.model_name = model_name
        self.distance_metric = distance_metric

    def initialize(self) -> None:
        """Inicializa DeepFace (lazy loading por defecto, pero podemos precargar)"""
        logger.info(f"Inicializando DeepFace con modelo {self.model_name}")
        # Build model forces it to load into memory
        DeepFace.build_model(self.model_name)
        logger.info("DeepFace inicializado correctamente")

    def process_face(self, face_img: Any, gallery: List[Dict[str, Any]]) -> EngineResultContract:
        start_time = time.time()

        try:
            # 1. Representación / Embedding
            # Usamos enforce_detection=False porque asumimos que YOLO o InsightFace ya detectaron el rostro
            objs = DeepFace.represent(img_path=face_img, model_name=self.model_name, enforce_detection=False)

            if not objs:
                logger.debug("DeepFace no pudo representar la imagen proporcionada.")
                return EngineResultContract(
                    engine="deepface",
                    model_name=self.model_name,
                    detected_human=False,
                    processing_ms=int((time.time() - start_time) * 1000)
                )

            # Tomar el primer rostro
            embedding = objs[0]["embedding"]

            # 2. Matching contra galería
            # Podríamos implementar un cosine similarity nativo de numpy igual que en InsightFace,
            # pero dado que el requerimiento pide verificar si está en la zona gris,
            # haremos la comparación manualmente aquí para tener el score de similitud (1 - distancia_coseno)
            import numpy as np
            best_match_id = None
            best_embedding_id = None
            best_observed_id = None
            best_observed_embedding_id = None

            best_similarity_persona = -1.0
            best_similarity_observed = -1.0
            best_observed_label = "unknown"
            best_observed_risk = "low"

            for item in gallery:
                if item.get('engine') != 'deepface':
                    continue

                gal_embed = np.array(item['embedding'], dtype=np.float32)
                embed_np = np.array(embedding, dtype=np.float32)

                # Similitud Coseno
                similarity = np.dot(embed_np, gal_embed) / (np.linalg.norm(embed_np) * np.linalg.norm(gal_embed))

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
                        best_observed_label = item.get('current_label', 'unknown')
                        best_observed_risk = item.get('risk_level', 'low')

            max_similarity = max(best_similarity_persona, best_similarity_observed)

            return EngineResultContract(
                engine="deepface",
                model_name=self.model_name,
                model_version="latest",
                detected_human=True,
                similarity=float(max_similarity) if max_similarity != -1.0 else None,
                similarity_persona=float(best_similarity_persona) if best_similarity_persona != -1.0 else None,
                similarity_observed=float(best_similarity_observed) if best_similarity_observed != -1.0 else None,
                candidate_persona_id=best_match_id,
                candidate_persona_embedding_id=best_embedding_id,
                candidate_observed_id=best_observed_id,
                candidate_observed_embedding_id=best_observed_embedding_id,
                embedding=embedding,
                embedding_dim=len(embedding),
                processing_ms=int((time.time() - start_time) * 1000),
                raw_response={"face_confidence": objs[0].get("face_confidence"),
                              "sim_persona": float(best_similarity_persona), "sim_observed": float(best_similarity_observed),
                              "observed_label": best_observed_label, "observed_risk": best_observed_risk}
            )

        except ValueError as e:
            logger.error(f"Error procesando rostro con DeepFace: {e}")
            return EngineResultContract(
                engine="deepface",
                model_name=self.model_name,
                detected_human=False,
                processing_ms=int((time.time() - start_time) * 1000),
                raw_response={"error": str(e)}
            )

# Instancia global
deepface_service = DeepFaceService()
