from __future__ import annotations

import logging
import os
from typing import Optional

from logtail import LogtailHandler

_LOGGER_NAME = "rpa_newcon"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger_name = name or _LOGGER_NAME
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    source_token = os.getenv("BETTERSTACK_TOKEN")
    host = os.getenv("BETTERSTACK_HOST")

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if source_token and host:
        betterstack_handler = LogtailHandler(
            source_token=source_token,
            host=host,
        )
        betterstack_handler.setFormatter(formatter)
        logger.addHandler(betterstack_handler)

    return logger