import pytest
from src.config.settings import Settings
from pydantic import ValidationError

def test_settings_successful_initialization(monkeypatch):
    """Test para verificar que las configuraciones de prueba se cargan correctamente."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_pass")
    monkeypatch.setenv("DB_DATABASE", "test_db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.db_host == "localhost"
    assert settings.db_user == "test_user"
    assert settings.log_level == "DEBUG"
    assert "test_user:test_pass@localhost:3306/test_db" in settings.database_url

def test_settings_missing_mandatory_field(monkeypatch):
    """Test para verificar que Settings arroja error si falta un campo mandatorio."""
    monkeypatch.delenv("DB_USER", raising=False)
    # Evitar leer el .env para este test, aunque pydantic-settings lo intentará,
    # el borrar las variables no siempre lo garantiza si lee el archivo.
    # Usaremos monkeypatching para limpiar variables de entorno locales

    # Para aislar, cambiamos el comportamiento para no leer env file o forzar error
    import os
    if os.path.exists(".env"):
        os.rename(".env", ".env.bak")

    try:
        with pytest.raises(ValidationError):
            Settings()
    finally:
        if os.path.exists(".env.bak"):
            os.rename(".env.bak", ".env")
