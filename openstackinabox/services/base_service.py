import logging

from stackinabox.services.service import StackInABoxService


logger = logging.getLogger(__name__)


class BaseService(StackInABoxService):

    def __init__(self, *args, **kwargs):
        super(BaseService, self).__init__(*args, **kwargs)

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

    def log_request(self, uri, request):
        self.log_debug('Received request {0}'.format(uri))
        self.log_debug('Received headers {0}'.format(request.headers))
