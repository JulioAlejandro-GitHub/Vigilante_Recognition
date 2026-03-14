from sqlalchemy.orm import Session
from sqlalchemy import func
from src.db.session import engine
from src.repositories.models import ObservedIdentityModel
from src.core.enums.domain import ObservedStatusEnum
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

def run_observed_identity_housekeeping() -> None:
    """
    Ejecuta el proceso de housekeeping para las identidades observadas.
    Archiva o elimina las identidades que han superado su tiempo de retención.
    """
    logger.info("Iniciando housekeeping de identidades observadas...")

    mode = settings.observed_housekeeping_mode.lower()
    batch_size = settings.observed_housekeeping_batch_size

    with Session(engine) as db:
        try:
            # Buscar identidades expiradas
            expired_query = db.query(ObservedIdentityModel).filter(
                ObservedIdentityModel.status == ObservedStatusEnum.ACTIVE,
                ObservedIdentityModel.expires_at != None,
                ObservedIdentityModel.expires_at < func.now()
            )

            count = expired_query.count()
            if count == 0:
                logger.info("No hay identidades observadas expiradas para procesar.")
                return

            logger.info(f"Se encontraron {count} identidades observadas expiradas. Modo de housekeeping: {mode}")

            processed = 0
            while True:
                batch = expired_query.limit(batch_size).all()
                if not batch:
                    break

                for identity in batch:
                    if mode == "archive":
                        identity.status = ObservedStatusEnum.EXPIRED
                        # Si quisiéramos borrar los embeddings para liberar espacio, podríamos hacerlo aquí
                        # identity.embeddings.clear()
                    elif mode == "delete":
                        db.delete(identity)

                    processed += 1

                db.commit()
                logger.info(f"Procesadas {processed}/{count} identidades.")

            logger.info(f"Housekeeping completado exitosamente. {processed} identidades afectadas.")

        except Exception as e:
            db.rollback()
            logger.error(f"Error durante el housekeeping de identidades observadas: {e}", exc_info=True)
