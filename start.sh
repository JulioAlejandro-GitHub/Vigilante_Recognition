#!/bin/bash
set -e

echo "============================================="
echo "Iniciando Vigilante Recognition Architecture"
echo "============================================="

# 1. Verificar entorno virtual
if [ -d ".venv" ]; then
    echo "[INFO] Entorno virtual encontrado. Activando..."
    source .venv/bin/activate
else
    echo "[WARNING] No se encontró el entorno virtual '.venv'."
    echo "[WARNING] Asegúrate de que las dependencias están instaladas globalmente o crea uno."
fi

# 2. Verificar variables de entorno
if [ ! -f ".env" ]; then
    echo "[ERROR] No se encontró el archivo .env"
    echo "Copia .env.example a .env y configura tus credenciales."
    exit 1
fi

# 3. Verificar directorios de datos necesarios
mkdir -p data/frames
echo "[INFO] Directorio de frames listo."

# 4. Iniciar la aplicación
echo "[INFO] Arrancando aplicación..."
export PYTHONPATH=.
exec python3 src/app/main.py
