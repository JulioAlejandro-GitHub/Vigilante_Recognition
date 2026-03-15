import pytest
from src.config.settings import settings
from src.core.enums.domain import ProcessingStatusEnum, EngineEnum, FinalLabelEnum, ObservedStatusEnum, ObservedLabelEnum, RiskLevelEnum
from src.repositories.models import ObservedIdentityModel, ObservedIdentityEmbeddingModel

def test_observed_identity_layer_settings():
    # Verificar la configuración requerida para la capa de identidad observada
    assert hasattr(settings, 'enable_observed_identity')
    assert settings.enable_observed_identity is True

    assert hasattr(settings, 'observed_identity_threshold')
    assert settings.observed_identity_threshold == 0.55

    assert hasattr(settings, 'known_person_threshold')
    assert settings.known_person_threshold == 0.60

    assert hasattr(settings, 'observed_identity_max_embeddings')
    assert settings.observed_identity_max_embeddings == 10

def test_observed_identity_models_exist():
    # Verificar que los modelos necesarios para la identidad observada existan
    assert hasattr(ObservedIdentityModel, 'observed_identity_id')
    assert hasattr(ObservedIdentityModel, 'status')
    assert hasattr(ObservedIdentityModel, 'current_label')
    assert hasattr(ObservedIdentityModel, 'risk_level')
    assert hasattr(ObservedIdentityModel, 'times_seen')

    assert hasattr(ObservedIdentityEmbeddingModel, 'observed_identity_embedding_id')
    assert hasattr(ObservedIdentityEmbeddingModel, 'embedding_vector')
    assert hasattr(ObservedIdentityEmbeddingModel, 'engine')

def test_enums_used_in_observed_identity():
    # Verificar la existencia de enumeraciones esenciales usadas
    assert hasattr(ObservedStatusEnum, 'ACTIVE')
    assert hasattr(ObservedLabelEnum, 'UNKNOWN')
    assert hasattr(ObservedLabelEnum, 'SOSPECHOSO')
    assert hasattr(RiskLevelEnum, 'LOW')
    assert hasattr(RiskLevelEnum, 'HIGH')
    assert hasattr(EngineEnum, 'INSIGHTFACE')
    assert hasattr(EngineEnum, 'DEEPFACE')
