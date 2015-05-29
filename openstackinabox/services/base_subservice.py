import logging

from openstackinabox.services.base_service import BaseService


class BaseSubServiceException(Exception):
    pass


class InvalidParentService(BaseSubServiceException):
    pass


class InvalidModelTarget(BaseSubServiceException):
    pass


class BaseSubService(BaseService):

    def __init__(self, name, parent):
        super(BaseSubService, self).__init__(name)

        if not isinstance(parent, BaseService):
            raise InvalidParentService(
                'Parent service must be of type '
                'openstackinabox.services.base_service.BaseService or '
                'openstackinabox.services.base_subservice.BaseSubService')

        self.__parent = parent
        self.__is_base = False

    def __get_parent(self):
        return self.__parent

    def get_root(self):
        if self.__parent is None:
            raise InvalidParentService('Missing parent service')

        return self.__parent if self.__parent.is_base else \
            self.__parent.get_root()

    def get_model(self):
        if self.__parent is None:
            raise InvalidParentService('Missing parent service')

        return self.__parent.model

    def set_model(self, value):
        raise InvalidModelTarget(
            'Models can only be set on the primary service node')

    def get_route_regex(self):
        raise NotImplementedError
