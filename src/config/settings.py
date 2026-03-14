from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación.
    Lee valores desde el archivo .env o variables de entorno.
    """

    # Base de datos
    db_host: str = Field(..., description="Host de la base de datos MySQL")
    db_port: int = Field(default=3306, description="Puerto de la base de datos MySQL")
    db_user: str = Field(..., description="Usuario de la base de datos")
    db_password: str = Field(..., description="Contraseña de la base de datos")
    db_database: str = Field(..., description="Nombre de la base de datos")

    # Logging
    log_level: str = Field(default="INFO", description="Nivel de logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

    # Observability
    enable_healthcheck: bool = Field(default=True, description="Habilita el monitor de salud en background")
    healthcheck_interval: int = Field(default=60, description="Intervalo en segundos para el healthcheck")

    # Detección de Rostros
    face_min_width: int = Field(default=30, description="Ancho mínimo del bounding box del rostro")
    face_min_height: int = Field(default=30, description="Alto mínimo del bounding box del rostro")
    face_padding_percent: float = Field(default=0.10, description="Porcentaje de padding para recortar el rostro")

    # Reconocimiento
    default_rtsp_port: int = Field(default=554, description="Puerto RTSP por defecto a usar si la cámara no lo especifica")
    insightface_threshold: float = Field(default=0.60, description="Umbral para coincidencia segura en InsightFace")
    insightface_ambiguous_threshold: float = Field(default=0.50, description="Umbral inferior para considerar resultado ambiguo y lanzar DeepFace")
    deepface_threshold: float = Field(default=0.60, description="Umbral para coincidencia segura en DeepFace")

    # Re-Identificación Observados (No enrolados)
    enable_observed_reid: bool = Field(default=True, description="Habilita la re-identificación de personas observadas no enroladas")
    known_person_threshold: float = Field(default=0.60, description="Umbral para considerar coincidencia segura con persona enrolada")
    observed_identity_threshold: float = Field(default=0.55, description="Umbral para considerar coincidencia segura con identidad observada")
    observed_identity_max_embeddings: int = Field(default=10, description="Número máximo de embeddings a guardar por identidad observada")
    observed_identity_min_quality: float = Field(default=0.50, description="Calidad mínima del rostro para guardar embedding de observado")

    # Storage y Media
    storage_enabled: bool = Field(default=True, description="Habilitar subida de media a Storage Service")
    storage_service_base_url: str = Field(default="http://localhost:8000", description="URL base de Vigilante Storage")
    storage_upload_timeout_seconds: int = Field(default=10, description="Timeout en segundos para uploads HTTP")
    storage_source_service: str = Field(default="recognition_service_1", description="Identificador del servicio que envía la media")
    storage_base_path: str = Field(default="storage", description="Directorio base transitorio o legacy para media")
    media_base_url: str = Field(default="/media", description="URL pública base legacy")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Genera la URL de conexión para SQLAlchemy."""
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_database}"

# Instancia global de settings
settings = Settings()
