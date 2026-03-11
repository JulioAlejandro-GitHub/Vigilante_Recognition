import threading
import time
import os
import psutil
from src.utils.logger import get_logger
from src.recognition_queue.queue import recognition_queue

logger = get_logger(__name__)

class HealthCheckMonitor(threading.Thread):
    """
    Monitor de salud del sistema.
    Corre en background y loggea periódicamente métricas básicas del sistema y del proceso.
    """
    def __init__(self, interval_seconds=60):
        super().__init__()
        self.interval_seconds = interval_seconds
        self.running = False
        self.daemon = True # Termina cuando el thread principal termina
        self.process = psutil.Process(os.getpid())

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        logger.info(f"HealthCheckMonitor iniciado. Reportando métricas cada {self.interval_seconds} segundos.")

        while self.running:
            try:
                # 1. Uso de CPU
                cpu_percent = self.process.cpu_percent(interval=1.0)

                # 2. Uso de Memoria (RSS en MB)
                mem_info = self.process.memory_info()
                memory_mb = mem_info.rss / (1024 * 1024)

                # 3. Hilos activos
                active_threads = threading.active_count()

                # 4. Estado de la cola de reconocimiento
                q_size = recognition_queue.qsize()

                # Reporte
                logger.info(
                    f"HEALTH CHECK: CPU: {cpu_percent:.1f}% | Mem: {memory_mb:.1f} MB | "
                    f"Threads: {active_threads} | Cola jobs: {q_size}"
                )

                # Dormir hasta el siguiente ciclo (dividido para poder reaccionar rápido a self.running)
                for _ in range(self.interval_seconds - 1):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error en HealthCheckMonitor: {e}")
                time.sleep(5)

        logger.info("HealthCheckMonitor detenido.")

health_monitor = HealthCheckMonitor(interval_seconds=60)
