import logging


logger = logging.getLogger(__name__)


class BaseModelExceptions(Exception):
    pass


class BaseModel(object):

    def __init__(self, name):
        self.name = name

    def log_debug(self, msg):
        logger.debug('{0} ({1}): {2}'
                     .format(self.name, id(self), msg))

    def log_info(self, msg):
        logger.info('{0} ({1}): {2}'
                    .format(self.name, id(self), msg))

    def log_exception(self, msg):
        logger.exception('{0} ({1}): {2}'
                         .format(self.name, id(self), msg))

    def log_error(self, msg):
        logger.error('{0} ({1}): {2}'
                     .format(self.name, id(self), msg))
