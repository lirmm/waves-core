import logging

logger = logging.getLogger(__name__)


class WavesException(Exception):
    """
    Waves base exception class, simply log exception in standard web logs
    TODO: This class may be obsolete depending of running / logging configuration
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.exception('[%s] - %s', self.__class__.__name__, self)
