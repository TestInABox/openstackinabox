"""
OpenStack Keystone v2 Service
"""
import json
import re
import uuid

import six
from six.moves.urllib import parse

from openstackinabox.models.keystone import KeystoneModel
from openstackinabox.services.base_service import BaseService
from openstackinabox.services.keystone.v2.base import KeystoneV2ServiceBase
from openstackinabox.services.keystone.v2.exceptions import *
from openstackinabox.services.keystone.v2.tenants import (
    KeystoneV2ServiceTenants
)
from openstackinabox.services.keystone.v2.users import (
    KeystoneV2ServiceUsers
)


class KeystoneV2Service(KeystoneV2ServiceBase):

    def __init__(self):
        super(KeystoneV2Service, self).__init__('keystone/v2.0')
        self.log_info('initializing keystone v2.0 services...')
        self.model = KeystoneModel()
        self.__subservices = [
            {
                'path': re.compile('^/tenants'),
                'service': KeystoneV2ServiceTenants(self.model)
            },
            {
                'path': re.compile('^/users'),
                'service': KeystoneV2ServiceUsers(self.model)
            }
        ]
        for subservice in self.__subservices:
            self.register_subservice(
                subservice['path'],
                subservice['service']
            )

        self.log_info('initialized')
