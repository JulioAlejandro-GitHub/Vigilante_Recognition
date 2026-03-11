FROM python:3.10-slim

# Evitar que python escriba pyc y usar buffer en stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para OpenCV y compilar librerías de ML
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias primero (aprovechar cache de Docker)
COPY requirements/base.txt requirements/streaming.txt ./requirements/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt && \
    pip install --no-cache-dir -r requirements/streaming.txt

# Copiar el resto del código
COPY . .

# Preparar directorios de datos
RUN mkdir -p data/frames

# Variables de entorno por defecto
ENV PYTHONPATH=/app

# Comando de inicio
CMD ["python", "src/app/main.py"]