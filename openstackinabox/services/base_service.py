import logging

from stackinabox.services.service import StackInABoxService


logger = logging.getLogger(__name__)


class BaseService(StackInABoxService):

    def __init__(self, name):
        super(BaseService, self).__init__(name)
        self.__is_base = True

    def log_debug(self, msg):
        logger.debug('{0} ({1}): {2}'
                     .format(self.name, id(self), msg))

    def log_info(self, msg):
        logger.info('{0} ({1}): {2}'
                    .format(self.name, id(self), msg))

    def log_exception(self, msg):
        logger.exception('{0} ({1}): {2}'
                         .format(self.name, id(self), msg))

    def log_request(self, uri, request):
        self.log_debug('Received request {0}'.format(uri))
        self.log_debug('Received headers {0}'.format(request.headers))

    @property
    def is_base(self):
        return self.__is_base

    @property
    def model(self):
        return self.get_model()

    @model.setter
    def model(self, value):
        self.set_model(value)

    def get_model():
        raise NotImplementedError

    def set_model(self, value):
        raise NotImplementedError

    def add_subservice(self, subservice):
        regex = subservice.get_route_regex()
        self.register_subservice(regex, subservice)

    def add_subservices(self, subservices):
        for subservice in subservices:
            self.add_subservice(subservice)
