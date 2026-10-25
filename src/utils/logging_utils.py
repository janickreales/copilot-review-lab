"""Logging homogéneo para notebooks y librerías del pipeline."""

import logging

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Devuelve un logger con un único handler de consola.

    Llamarlo varias veces con el mismo nombre no duplica handlers, algo
    habitual cuando un notebook se re-ejecuta en la misma sesión.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
