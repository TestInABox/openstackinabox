import logging


logger = logging.getLogger(__name__)


class BaseModelExceptions(Exception):
    """
    Base Exception for all the model exceptions
    """


class BaseModel(object):
    """
    Base Model for common operations
    """

    def __init__(self, name):
        """
        :param unicode name: name of the model
        """
        self.name = name

    def log_debug(self, msg):
        """
        Enter a debug message into the log

        :param unicode msg: message to log
        """
        logger.debug('{0} ({1}): {2}'
                     .format(self.name, id(self), msg))

    def log_info(self, msg):
        """
        Enter a informational message into the log

        :param unicode msg: message to log
        """
        logger.info('{0} ({1}): {2}'
                    .format(self.name, id(self), msg))

    def log_exception(self, msg):
        """
        Enter a exception message into the log

        :param unicode msg: message to log
        """
        logger.exception('{0} ({1}): {2}'
                         .format(self.name, id(self), msg))

    def log_error(self, msg):
        """
        Enter a error message into the log

        :param unicode msg: message to log
        """
        logger.error('{0} ({1}): {2}'
                     .format(self.name, id(self), msg))
