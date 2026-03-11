# Vigilante Recognition

Arquitectura fundacional para el sistema de reconocimiento facial orientado a eventos (Vigilante v2). Este repositorio sienta las bases limpias, modulares y mantenibles para la integración de streaming de video, detección y reconocimiento con InsightFace/DeepFace, y la persistencia centralizada en base de datos.

## Estructura del Proyecto

```
.
├── src/
│   ├── app/                    # Entrypoints y configuración de inicio
│   ├── cam_streaming/          # Módulo para leer streams RTSP/HTTP (Etapa 2)
│   ├── config/                 # Configuraciones centralizadas (Pydantic Settings)
│   ├── core/                   # Modelos de dominio e interfaces base
│   │   ├── enums/
│   │   ├── interfaces/
│   │   └── models/
│   ├── db/                     # Conexión a Base de Datos MySQL / SQLAlchemy
│   ├── engines/                # Implementaciones de motores de reconocimiento (DeepFace, InsightFace)
│   ├── recognition_orchestrator/# Orquestador de trabajos (Etapa 2)
│   ├── recognition_queue/      # Colas de procesamiento (Etapa 2)
│   ├── repositories/           # Patrón repositorio para acceso a datos
│   ├── services/               # Lógica de negocio (Etapa 2)
│   ├── utils/                  # Utilidades como Logging centralizado
│   └── yolo_detector/          # Detección de personas usando YOLO (Etapa 2)
├── tests/                      # Pruebas unitarias
├── .env.example                # Ejemplo de variables de entorno requeridas
├── requirements/               # Archivos de requerimientos divididos por entorno
└── Vigilante_v2_configurable.sql # Schema de Base de Datos Base
```

## Requisitos Previos

- Python 3.10+
- MySQL 8+ / MariaDB 10+
- `venv` para el manejo de entornos virtuales local

## Instrucciones de Instalación y Ejecución

1. **Clonar y preparar el entorno**
   Crea y activa tu entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Base de Datos**
   Asegúrate de que tu servicio de MySQL/MariaDB esté activo e inicializa el esquema base:
   ```bash
   mysql -u tu_usuario -p < Vigilante_v2_configurable.sql
   ```
   **Nota**: Deberás insertar datos en la tabla `camara` (con `estado = 'Activo'`) para que el módulo de streaming funcione y pueda leer RTSP/Webcams.

3. **Ejecutar usando el script de Operaciones (Recomendado)**
   El script creará el entorno virtual, instalará dependencias, creará tu archivo `.env` base y ejecutará la aplicación de forma segura:
   ```bash
   ./start.sh
   ```

   **Opcional: Ejecución manual paso a paso**
   ```bash
   # Configurar variables (luego editar credenciales MySQL)
   cp .env.example .env

   # Activar venv e instalar deps
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements/base.txt
   pip install -r requirements/streaming.txt

   # Correr app
   python src/app/main.py
   ```

## Estabilidad y Observabilidad
Esta versión incluye las siguientes mejoras productivas para facilitar el debugging y la escalabilidad:
- **Healthchecks**: Un monitor en background vigilará continuamente la conexión DB, la cola de memoria y la salud de los threads RTSP. Configurable vía `ENABLE_HEALTHCHECK` y `HEALTHCHECK_INTERVAL`.
- **Structured Logging**: Sistema de logs enriquecidos. Errores críticos y eventos relevantes ahora inyectan contexto explícito (ej: `camera_id` o `job_id`) en formato JSON.
- **Tolerancia a fallos**:
  - Los Streams RTSP implementan reconexión con "Exponential Backoff" para no saturar el CPU o la red ante caídas.
  - El Orquestador captura caídas por engine fallido, y realiza rollback seguro a nivel de DB para mantener la integridad relacional de eventos.

Al arrancar se intentará conectar a las cámaras activas configuradas en BD. Las detecciones de YOLO se encolan hacia la etapa de reconocimiento, que evalúa a los candidatos usando InsightFace, y apoya con DeepFace en rangos ambiguos.
