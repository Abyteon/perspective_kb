import logging
import time


def timestamp_now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def get_logger(name="perspective_kb"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
