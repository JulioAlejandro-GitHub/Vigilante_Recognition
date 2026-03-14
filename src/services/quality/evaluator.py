import cv2
import numpy as np
from typing import Dict, Any, Tuple
from enum import Enum
from src.config.settings import settings
from src.core.enums.domain import PerfilEnum
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FaceQualityDecision(str, Enum):
    USABLE_FOR_ALL = "usable_for_all"
    USABLE_FOR_STORAGE_ONLY = "usable_for_storage_only"
    DISCARDED = "discarded"

class FaceQualityEvaluator:
    """
    Evalúa la calidad de un rostro detectado basándose en tamaño, blur, score del detector,
    pose (perfil) y oclusión aproximada.
    """

    @staticmethod
    def compute_blur(img: np.ndarray) -> float:
        """Calcula el blur usando la varianza laplaciana. Mayor es más nítido."""
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    @staticmethod
    def compute_pose_and_perfil(insight_face_obj: Any) -> Tuple[float, PerfilEnum]:
        """
        Estima la pose y mapea a PerfilEnum basándose en insightface pose.
        Devuelve (pose_score, perfil)
        Pose score es más alto (cercano a 1.0) si es más frontal.
        """
        if not hasattr(insight_face_obj, 'pose') or insight_face_obj.pose is None:
            return (0.5, PerfilEnum.UNDETECTED)

        pitch, yaw, roll = insight_face_obj.pose

        # yaw (giro izquierda/derecha). Valores abs más grandes -> más perfil
        # pitch (arriba/abajo)
        # roll (inclinación)

        abs_yaw = abs(yaw)

        if abs_yaw > 45:
            # Perfil marcado
            perfil = PerfilEnum.LEFT if yaw > 0 else PerfilEnum.RIGHT # Depende de convención de insightface, aproximación
            pose_score = max(0.0, 1.0 - (abs_yaw / 90.0)) # penaliza pose
        else:
            perfil = PerfilEnum.FRONT
            # Si es frontal (yaw cerca a 0), score alto
            pose_score = max(0.5, 1.0 - (abs_yaw / 90.0))

        return float(pose_score), perfil

    @staticmethod
    def compute_occlusion(insight_face_obj: Any, face_w: int, face_h: int) -> float:
        """
        Estima oclusión basada en landmarks de insightface.
        Retorna occlusion_score (1.0 = sin oclusión, 0.0 = muy ocluido)
        """
        if not hasattr(insight_face_obj, 'kps') or insight_face_obj.kps is None:
            return 0.5

        kps = insight_face_obj.kps
        # Insightface usualmente devuelve 5 puntos
        if len(kps) < 5:
            return 0.2

        # Oclusión heurística simple: si los keypoints están muy agrupados o faltan
        # Aquí asumimos que si insightface detectó la cara y dio kps, no hay una oclusión masiva
        # Pero podemos penalizar si el ratio de kps bounds vs crop es anómalo

        kps_x = [p[0] for p in kps]
        kps_y = [p[1] for p in kps]

        kps_w = max(kps_x) - min(kps_x)
        kps_h = max(kps_y) - min(kps_y)

        if kps_w == 0 or kps_h == 0 or face_w == 0 or face_h == 0:
            return 0.2

        # Si los keypoints cubren muy poco de la cara, podría estar ocluido o ser mala detección
        w_ratio = kps_w / face_w
        h_ratio = kps_h / face_h

        if w_ratio < 0.2 or h_ratio < 0.2:
            return 0.4 # posible oclusión

        return 1.0

    @staticmethod
    def evaluate(face_img: np.ndarray, insight_face_obj: Any) -> Dict[str, Any]:
        """
        Evalúa un rostro y devuelve las métricas calculadas, el score global y la decisión.
        """
        h, w = face_img.shape[:2]

        # 1. Tamaño
        face_width = w
        face_height = h

        # 2. Blur
        blur_score = FaceQualityEvaluator.compute_blur(face_img)

        # 3. Pose
        pose_score, perfil = FaceQualityEvaluator.compute_pose_and_perfil(insight_face_obj)

        # 4. Detector score
        det_score = float(insight_face_obj.det_score) if hasattr(insight_face_obj, 'det_score') else 0.0

        # 5. Oclusión
        # El bbox del face obj es respecto a la imagen completa de entrada (person_crop), así que usamos el tamaño del face_crop_img real
        occlusion_score = FaceQualityEvaluator.compute_occlusion(insight_face_obj, w, h)

        # 6. Global Score (Fórmula ponderada)
        # Normalizamos blur rudimentariamente: asumimos que un blur_score sobre 150 es 1.0 (excelente)
        blur_norm = min(1.0, blur_score / 150.0)

        # Fórmula de calidad (configurable):
        # 40% det_score, 20% blur_norm, 20% pose_score, 20% occlusion
        quality_score = (0.4 * det_score) + (0.2 * blur_norm) + (0.2 * pose_score) + (0.2 * occlusion_score)

        metrics = {
            "face_width": face_width,
            "face_height": face_height,
            "blur_score": blur_score,
            "face_detector_score": det_score,
            "pose_score": pose_score,
            "occlusion_score": occlusion_score,
            "quality_score": quality_score,
            "perfil": perfil,
            "decision": FaceQualityDecision.USABLE_FOR_ALL,
            "discard_reason": None
        }

        if not settings.enable_face_quality_filter:
            return metrics

        # Política de decisión
        if det_score < settings.min_face_detector_score:
            metrics["decision"] = FaceQualityDecision.DISCARDED
            metrics["discard_reason"] = f"det_score {det_score:.2f} < {settings.min_face_detector_score}"
            return metrics

        if blur_score < settings.min_blur_score:
            metrics["decision"] = FaceQualityDecision.DISCARDED
            metrics["discard_reason"] = f"blur_score {blur_score:.2f} < {settings.min_blur_score}"
            return metrics

        if face_width < settings.face_min_width or face_height < settings.face_min_height:
             metrics["decision"] = FaceQualityDecision.DISCARDED
             metrics["discard_reason"] = f"size {face_width}x{face_height} < {settings.face_min_width}x{settings.face_min_height}"
             return metrics

        if quality_score < settings.min_quality_score_for_matching:
            metrics["decision"] = FaceQualityDecision.USABLE_FOR_STORAGE_ONLY
            metrics["discard_reason"] = f"quality_score {quality_score:.2f} < {settings.min_quality_score_for_matching}"
            return metrics

        return metrics

face_quality_evaluator = FaceQualityEvaluator()
