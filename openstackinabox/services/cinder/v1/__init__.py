import re

from openstackinabox.services.cinder.v1 import base
from openstackinabox.models.cinder import model
from openstackinabox.services.cinder.v1 import volumes


class CinderV1Service(base.CinderV1ServiceBase):

    def __init__(self, keystone_service):
        super(CinderV1Service, self).__init__(keystone_service, 'cinder/v1')
        self.log_info('initializing cinder v1.0 services...')
        self.model = model.CinderModel(keystone_service.model)
        self.__subservices = [
            {
                'path': re.compile('^/volumes'),
                'service': volumes.CinderV1Volumes(
                    self.model,
                    keystone_service
                )
            }
        ]

        for subservice in self.__subservices:
            self.register_subservice(
                subservice['path'],
                subservice['service']
            )

        self.log_info('initialized')
