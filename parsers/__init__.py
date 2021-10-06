import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger_handler = logging.FileHandler('parsers.log', mode='a')
logger_handler.setLevel(logging.INFO)

logger_formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s')

logger_handler.setFormatter(logger_formatter)

logger.addHandler(logger_handler)
