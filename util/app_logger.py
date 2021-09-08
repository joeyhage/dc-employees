import logging
from os import environ
from logging.handlers import WatchedFileHandler
from pathlib import PurePath


# noinspection SpellCheckingInspection
def create_logger(name, is_dev):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if is_dev:
        handler = logging.StreamHandler()
    else:
        handler = WatchedFileHandler(filename=(str(PurePath(r'/var/log/' + environ['DOMAIN'] + '/flask.log'))))
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
