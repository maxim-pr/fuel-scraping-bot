import logging


def setup_logger(logger: logging.Logger):
    logger.setLevel(logging.INFO)

    logger_handler = logging.StreamHandler()
    logger_handler.setLevel(logging.INFO)

    logger_formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s'
    )

    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)
