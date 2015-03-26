"""
OpenStack Keystone v2 Service
"""
import json
import logging
import uuid

from stackinabox.services.service import StackInABoxService
from openstackinabox.models.keystone import KeystoneModel


logger = logging.getLogger(__name__)


class KeystoneV2Service(StackInABoxService):

    def __init__(self):
        super(KeystoneV2Service, self).__init__('keystone/v2.0')
        self.__id = uuid.uuid4()
        self.__model = KeystoneModel()

        self.register(StackInABoxService.GET,
                      '/tenants',
                      KeystoneV2Service.handle_list_tenants)
        self.register(StackInABoxService.GET,
                      '/users',
                      KeystoneV2Service.handle_list_users)
        self.register(StackInABoxService.POST,
                      '/users',
                      KeystoneV2Service.handle_add_user)

    @property
    def model(self):
        return self.__model

    @model.setter
    def model(self, value):
        if isinstance(value, KeystoneModel):
            self.__model = value
        else:
            raise TypeError('model is not an instance of KeystoneModel')

    def handle_list_tenants(self, request, uri, headers):
        req_headers = request.headers
        '''
        200, 203 -> OK
        400 -> Bad Request: one or more required parameters
                            are missing or invalid
        401 -> not authorized
        403 -> forbidden (no permission)
        404 -> Not found
        405 -> Invalid Method
        413 -> Over Limit - too many items requested
        503 -> Service Fault
        '''
        logger.debug('KeystoneV2Service({0}): Received request {1}'
                     .format(self.__id, uri))
        logger.debug('KeystoneV2Service({0}): Received headers {1}'
                     .format(self.__id, request.headers))

        if 'x-auth-token' in req_headers:
            if req_headers['x-auth-token'] == self.model.get_admin_token():
                """
                Body on success:
                body = {
                    'tenants' : [ {'id': 01234,
                                   'name': 'bob',
                                   'description': 'joe bob',
                                   'enabled': True }]
                    'tenants_links': []
                }
                """
                response_body = {
                    'tenants': [tenant_info
                                for tenant_info in
                                self.model.get_tenants()],
                    'tenants_links': []
                }
                return (200, headers, json.dumps(response_body))

            else:
                return (401, headers, 'Not Authorized')

        else:
            return (403, headers, 'Forbidden')

    def handle_list_users(self, request, uri, headers):
        req_headers = request.headers
        '''
        '''
        logger.debug('KeystoneV2Service({0}): received request {1}'
                     .format(self.__id, uri))
        logger.debug('KeystoneV2Service({0}): Received headers {1}'
                     .format(self.__id, request.headers))

        def user_data_filter(user):
            logger.debug('Filtering data on {0}'.format(user))
            return {
                'userid': user['userid'],
                'enabled': user['enabled'],
                'username': user['username'],
                'email': user['email'],
            }

        if 'x-auth-token' in req_headers:
            try:
                user_data = self.model.validate_token_admin(
                    req_headers['x-auth-token'])

                logger.debug('KeystoneV2Service({0}): Token Valid for '
                             'tenantid {1}'
                             .format(self.__id, user_data['tenantid']))
                response_body = {
                    'users': [user_data_filter(user_info)
                              for user_info in
                              self.model.get_users_for_tenant_id(
                                  user_data['tenantid'])]
                }
                return (200, headers, json.dumps(response_body))

            except Exception as ex:
                logger.exception('User List Failure')
                return (401, headers, 'Not Authorized')
        else:
            return (403, headers, 'Forbidden')

    def handle_add_user(self, request, uri, headers):
        req_headers = request.headers
        '''
        201 -> created
        400 -> Bad Request - missing one or more element, or values were invalid
        401 -> unauthorized
        403 -> forbidden (no permission)
        404 -> not found
        405 -> invalid method
        409 -> user already exists
        413 -> over limit - number of items returned is too large
        415 -> bad media type
        503 -> service not available

        Note: Admins can add up to 100 users to an account.

        Required:
            x-auth-token

        Body:
        {
            'username': <username>,
            'email': <email>,
            'enabled': True/False,
            'OS-KSADM:password': <string>
        }

        Note: password is optional

        Spec:
            username:
                must start with a letter
                must be at least 1 character long
                may contain: upper and lower case characters and ._@-
            password:
                must start with a letter
                must be at least 8 characters long
                must contain 1 upper case, 1 lowercase, and 1 numeric value
                may contain: .-@_

        Response:
        {
            'user': {
                'username': <username>,
                'OS-KSADM:password': <password>,
                'email': <email>
                'RAX-AUTH:defaultRegion': <region>,
                'RAX-AUTH:domainId': <domain>,
                'id': <id>,
                'enabled': True/False
            }
        }
        '''
        logger.debug('KeystoneV2Service({0}): received request {1}'
                     .format(self.__id, uri))
        logger.debug('KeystoneV2Service({0}): received headers {1}'
                     .format(self.__id, request.headers))

        if 'x-auth-token' in req_headers:
            try:
                auth_token = req_headers['x-auth-token']

                user_data = self.model.validate_token(auth_token)

                logger.debug('token {0} maps to tenant {1} and userid {2}'
                             .format(auth_token,
                                     user_data['tenantid'],
                                     user_data['userid']))

            except Exception as ex:
                logger.exception('bad token lookup')
                return (401, headers, 'Not Authorized')

            current_user = self.model.get_user_by_id(user_data['tenantid'],
                                                     user_data['userid'])

            req_body = request.body.decode('utf-8')
            json_data = json.loads(req_body)

            try:
                username = json_data['user']['username']
                email = json_data['user']['email']
                enabled = json_data['user']['enabled']

            except LookupError:
                logger.exception('KeystoneV2Service({0}): missing parameter'
                                 .format(self.__id))
                return (400, headers, 'bad request')

            if username == current_user['username']:
                return (409, headers, 'user already exists')

            if not self.model.validate_username(username):
                logger.debug('KeystoneV2Service({0}): username invalid'
                             .format(self.__id))
                return (400, headers, 'bad request')

            try:
                password = json_data['user']['OS-KSADM:password']
            except LookupError:
                password = None
           
            if password is not None:
                if not self.model.validate_password(password):
                    logger.debug('KeystoneV2Service({0}): invalid password'
                                 .format(self.__id))
                    return (400, headers, 'bad request')

            try:
                user_info = self.model.add_user(
                    tenantid=current_user['tenantid'],
                    username=username,
                    email=email,
                    password=password,
                    enabled=enabled)

                return (201, headers, 'ok')

            except Exception as ex:
                logger.exception('User Add Failure')
                # is 404 correct?
                return (404, headers, 'failed to add user')
        else:
            return (403, headers, 'Forbidden')
