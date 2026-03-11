#!/bin/bash
set -e

# Imprimir banner
echo "=================================================="
echo "    Iniciando Vigilante Recognition Architecture   "
echo "=================================================="

# 1. Verificar .env
if [ ! -f ".env" ]; then
    echo "⚠️  ADVERTENCIA: Archivo .env no encontrado. Creando a partir de .env.example..."
    cp .env.example .env
    echo "⚠️  Por favor, asegúrate de editar .env con tus credenciales de Base de Datos."
    echo "    Puedes detener este script con Ctrl+C ahora para editarlo, o continuar si usas los defaults."
    sleep 3
fi

# 2. Verificar y Crear Entorno Virtual
if [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv .venv
fi

# Activar venv
echo "🔄 Activando entorno virtual..."
source .venv/bin/activate

# 3. Instalar Dependencias
echo "📥 Instalando dependencias base y de streaming..."
pip install --upgrade pip > /dev/null
pip install -r requirements/base.txt > /dev/null
pip install -r requirements/streaming.txt > /dev/null

# 4. Iniciar Aplicación
echo "🚀 Arrancando sistema..."
export PYTHONPATH=.
python src/app/main.py
