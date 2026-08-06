"""Configuração de logging do app.

Os erros são registrados no arquivo ciclo.log (gitignored) para diagnóstico,
sem poluir a interface do terminal.
"""
import logging
from logging.handlers import RotatingFileHandler

LOG_FILE = "ciclo.log"


def _configurar_logger() -> logging.Logger:
    logger = logging.getLogger("ciclo")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    try:
        handler = RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
    except Exception:
        # Se não for possível gravar o arquivo de log, segue sem logging.
        pass

    return logger


logger = _configurar_logger()
