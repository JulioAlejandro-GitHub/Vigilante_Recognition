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

    # Reconocimiento
    default_rtsp_port: int = Field(default=554, description="Puerto RTSP por defecto a usar si la cámara no lo especifica")
    insightface_threshold: float = Field(default=0.60, description="Umbral para coincidencia segura en InsightFace")
    insightface_ambiguous_threshold: float = Field(default=0.50, description="Umbral inferior para considerar resultado ambiguo y lanzar DeepFace")
    deepface_threshold: float = Field(default=0.60, description="Umbral para coincidencia segura en DeepFace")

    # Storage y Media
    storage_base_path: str = Field(default="storage", description="Directorio base para almacenamiento físico de las imágenes")
    media_base_url: str = Field(default="/media", description="URL pública base para consumir las imágenes desde UX")

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
