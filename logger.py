import logging

_fmt = '[%(asctime)s] [%(process)d] [%(levelname)s] [%(module)s] %(message)s'
_datefmt = '%Y-%m-%d %H:%M:%S %z'
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter(fmt=_fmt, datefmt=_datefmt))

logger = logging.getLogger()
logger.addHandler(_handler)
logger.setLevel(logging.INFO)
