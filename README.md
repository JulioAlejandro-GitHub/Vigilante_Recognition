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

2. **Instalar dependencias base**
   ```bash
   pip install -r requirements/base.txt
   ```

3. **Configuración de Variables de Entorno**
   Copia `.env.example` a `.env` y configura tus variables de entorno, específicamente las credenciales de la base de datos MySQL:
   ```bash
   cp .env.example .env
   # Edita .env con tus credenciales de MySQL
   ```

4. **Base de Datos**
   Asegúrate de que tu servicio de MySQL/MariaDB esté activo e inicializa el esquema base:
   ```bash
   mysql -u tu_usuario -p < Vigilante_v2_configurable.sql
   ```

5. **Ejecutar el Entrypoint (Bootstrap y Healthcheck)**
   El entrypoint principal valida la configuración, inicializa los logs y verifica la conexión a la base de datos:
   ```bash
   python src/app/main.py
   ```

Si todo funciona correctamente, verás en la consola los logs indicando "Bootstrap completado. Arquitectura lista para siguientes fases."
