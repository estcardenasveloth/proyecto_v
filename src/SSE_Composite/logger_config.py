import logging
from logging.handlers import RotatingFileHandler
import os

LOG_FILE = os.path.join("src", "SSE_Composite", "static", "logs", "collector.log")

def setup_logger():
    logger = logging.getLogger("collector_logger")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # 1) Handler de consola
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        # 2) Handler de archivo rotativo
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        fh = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
        fh.setLevel(logging.INFO)  # por ejemplo, solo INFO y superiores al archivo
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


