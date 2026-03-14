from enum import Enum

class EstadoEnum(str, Enum):
    ACTIVO = 'activo'
    INACTIVO = 'inactivo'

class ObservedStatusEnum(str, Enum):
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    MERGED = 'merged'
    PROMOTED = 'promoted'
    EXPIRED = 'expired'

class ObservedLabelEnum(str, Enum):
    UNKNOWN = 'unknown'
    OBSERVED = 'observed'
    LADRON = 'ladron'
    SOSPECHOSO = 'sospechoso'
    PERSONA_INTERES = 'persona_interes'
    VISITANTE = 'visitante'
    PROVEEDOR = 'proveedor'

class RiskLevelEnum(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class CamaraUbicacionEnum(str, Enum):
    INGRESO = 'Ingreso'
    ESTADIA = 'Estadia'
    SALIDA = 'Salida'
    OTRO = 'Otro'

class CamaraEstadoEnum(str, Enum):
    ACTIVO = 'Activo'
    INACTIVO = 'Inactivo'

class CamaraProtocoloEnum(str, Enum):
    ONVIF = 'onvif'
    WEBCAM = 'webcam'
    RTSP = 'rtsp'
    ARCHIVO = 'archivo'
    DVR = 'dvr'

class RolEnum(str, Enum):
    ADMIN = 'admin'
    SUPERVISOR = 'supervisor'
    OPERADOR = 'operador'
    VIEWER = 'viewer'

class GenderEnum(str, Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'
    UNKNOWN = 'unknown'

class PersonaTipoEnum(str, Enum):
    SOCIO = 'socio'
    EMPLEADO = 'empleado'
    FAMILIA = 'familia'
    LADRON = 'ladron'
    OTRO = 'otro'

class EngineEnum(str, Enum):
    HUMAN = 'human'
    INSIGHTFACE = 'insightface'
    DEEPFACE = 'deepface'
    FACENET = 'facenet'
    ARCFACE = 'arcface'
    OTRO = 'otro'

class PerfilEnum(str, Enum):
    FRONT = 'front'
    LEFT = 'left'
    RIGHT = 'right'
    TOP = 'top'
    UNDETECTED = 'undetected'

class SourceTypeEnum(str, Enum):
    CAMERA = 'camera'
    VIDEO_FILE = 'video_file'
    DVR = 'dvr'
    UPLOAD = 'upload'
    API = 'api'

class SolicitudStatusEnum(str, Enum):
    PENDIENTE = 'pendiente'
    PROCESANDO = 'procesando'
    PROCESADA = 'procesada'
    ERROR = 'error'

class ProcessingStatusEnum(str, Enum):
    OK = 'ok'
    SIN_ROSTRO = 'sin_rostro'
    ERROR = 'error'
    INVALID_FACE_CROP = 'invalid_face_crop'
    MISSING_FACE_BBOX = 'missing_face_bbox'
    EMPTY_FACE_CROP = 'empty_face_crop'
    FACE_CROP_OUT_OF_BOUNDS = 'face_crop_out_of_bounds'
    FACE_TOO_SMALL = 'face_too_small'

class FinalLabelEnum(str, Enum):
    DESCONOCIDO = 'desconocido'
    IDENTIFICADO = 'identificado'
    LADRON = 'ladron'
    RECHAZADO = 'rechazado'
    REVISAR = 'revisar'

class EstadoValidacionEnum(str, Enum):
    VALIDO = 'valido'
    POR_VALIDAR = 'por_validar'
    INVALIDO = 'invalido'

class AssignedStatusEnum(str, Enum):
    SIN_ASIGNAR = 'sin_asignar'
    AUTO_ASIGNADO = 'auto_asignado'
    MANUAL_ASIGNADO = 'manual_asignado'
    ENROLADO_DESDE_EVENTO = 'enrolado_desde_evento'

class DataTypeEnum(str, Enum):
    STRING = 'string'
    TEXT = 'text'
    INT = 'int'
    DECIMAL = 'decimal'
    BOOLEAN = 'boolean'
    JSON = 'json'
    ENUM = 'enum'
    TIME = 'time'
    DATETIME = 'datetime'

class EventoTipoEnum(str, Enum):
    LADRON = 'ladron'
    DESCONOCIDO = 'desconocido'
    IDENTIFICADO = 'identificado'
    RECHAZADO = 'rechazado'
    REVISAR = 'revisar'
    CUALQUIER_RECONOCIMIENTO = 'cualquier_reconocimiento'

class CanalEnum(str, Enum):
    WHATSAPP = 'whatsapp'
    TELEGRAM = 'telegram'
    EMAIL = 'email'
    WEBHOOK = 'webhook'
    SMS = 'sms'
    OTRO = 'otro'

class EstadoEnvioEnum(str, Enum):
    PENDIENTE = 'pendiente'
    ENVIADO = 'enviado'
    ERROR = 'error'
