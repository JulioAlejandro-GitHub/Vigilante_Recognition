import urllib.parse
from typing import Optional
from src.config.settings import settings

def build_rtsp_url(camera) -> Optional[str]:
    """
    Construye la URL RTSP basada en los campos de la cámara, asegurándose
    de no quemar credenciales en código, usando los datos del objeto.
    """
    if camera.stream_url:
        return camera.stream_url

    if not camera.camara_hostname:
        return None

    # URL encoding de credenciales según la petición
    user = urllib.parse.quote(camera.camara_user) if camera.camara_user else ""
    password = urllib.parse.quote(camera.camara_pass) if camera.camara_pass else ""
    port = camera.camara_port if camera.camara_port else settings.default_rtsp_port

    # En caso de que no tenga usuario/password
    if user:
        credentials = f"{user}:{password}@"
    else:
        credentials = ""

    # Usar lógica de Dahua si el protocolo es "rtsp" u "onvif", u otras condiciones si aplica
    # Según requerimiento:
    # rtspUrl = `rtsp://${encodeURIComponent(camera.camara_user)}:${encodeURIComponent(camera.camara_pass)}@${camera.camara_hostname}:${camera.camara_port}/cam/realmonitor?channel=1&subtype=0`;

    rtsp_url = f"rtsp://{credentials}{camera.camara_hostname}:{port}/cam/realmonitor?channel=1&subtype=0"

    return rtsp_url
