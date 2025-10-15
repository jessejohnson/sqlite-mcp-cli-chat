from .logutil import setup_logging
import logging as slog
from settings import settings

if settings.IS_DEBUG:
    setup_logging()