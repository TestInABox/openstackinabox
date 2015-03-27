"""
OpenStack Keystone v2 Service
"""
import json
import logging
import re
import uuid

import six
from six.moves.urllib import parse
from stackinabox.services.service import StackInABoxService

from openstackinabox.models.keystone import KeystoneModel


logger = logging.getLogger(__name__)


class KeystoneV2Service(StackInABoxService):

    # USER_ID_PATH_REGEX = re.compile('^\/users\/[a-zA-Z]+[\w\.@-]*$')
    USER_ID_PATH_REGEX = re.compile('^\/users\/([0-9]+)$')

    def __init__(self):
        super(KeystoneV2Service, self).__init__('keystone/v2.0')
        self.log_info('initializing keystone v2.0 services...')
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
        self.register(StackInABoxService.GET,
                      KeystoneV2Service.USER_ID_PATH_REGEX,
                      KeystoneV2Service.handle_get_user_by_id)
        self.log_info('initialized')

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
        self.log_request(uri, request)

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
        self.log_request(uri, request)

        def user_data_filter(user):
            self.log_debug('Filtering data on {0}'.format(user))
            return {
                'id': user['userid'],
                'enabled': user['enabled'],
                'username': user['username'],
                'email': user['email'],
            }

        if 'x-auth-token' in req_headers:
            try:
                user_data = self.model.validate_token_admin(
                    req_headers['x-auth-token'])

                self.log_debug('Token Valid for tenantid {0}'
                               .format(user_data['tenantid']))

                parsed_uri = parse.urlparse(uri)
                query = parsed_uri.query

                if len(query) > 0:
                    query_data = parse.parse_qs(query)


                    if 'name' in query_data:
                        user_info = self.model.get_user_by_name(
                            user_data['tenantid'],
                            query_data['name'][0])
                        response_body = {
                            'user': user_data_filter(user_info)
                        }
                        return (200, headers, json.dumps(response_body))

                response_body = {
                    'users': [user_data_filter(user_info)
                              for user_info in
                              self.model.get_users_for_tenant_id(
                                  user_data['tenantid'])]
                }
                return (200, headers, json.dumps(response_body))

            except Exception as ex:
                self.log_exception('User List Failure')
                return (401, headers, 'Not Authorized')
        else:
            return (403, headers, 'Forbidden')

    def handle_add_user(self, request, uri, headers):
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
        self.log_request(uri, request)
        req_headers = request.headers

        if 'x-auth-token' in req_headers:
            try:
                auth_token = req_headers['x-auth-token']

                user_data = self.model.validate_token(auth_token)

                self.log_debug('token {0} maps to tenant {1} and userid {2}'
                               .format(auth_token,
                                       user_data['tenantid'],
                                       user_data['userid']))

            except Exception as ex:
                self.log_exception('bad token lookup')
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
                self.log_exception('missing parameter')
                return (400, headers, 'bad request')

            if username == current_user['username']:
                return (409, headers, 'user already exists')

            if not self.model.validate_username(username):
                self.log_debug('username invalid')
                return (400, headers, 'bad request')

            try:
                password = json_data['user']['OS-KSADM:password']
            except LookupError:
                password = None
           
            if password is not None:
                if not self.model.validate_password(password):
                    self.log_debug('invalid password')
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
                self.log_exception('User Add Failure')
                # is 404 correct?
                return (404, headers, 'failed to add user')
        else:
            return (403, headers, 'Forbidden')

    @staticmethod
    def get_user_id_from_path(uri_path):
        uri_matcher =  KeystoneV2Service.USER_ID_PATH_REGEX.match(uri_path)
        userid =  uri_matcher.groups()[0]
        return userid

    def handle_get_user_by_id(self, request, uri, headers):
        '''
        GET /v2.0/users/{userid}

        userid = model's userid value

        200 -> Request successfully completed
        203 -> Request successfully completed
        400 -> Bad request
        401 -> Unauthorized
        403 -> Forbidden
        404 -> Not Found
        405 -> Invalid Method
        413 -> over limit
        503 -> Service error

        No body

        response:
        {
            'user': {
                'RAX-AUTH:defaultRegion': <region>
                'RAX-AUTH:domainId': <domain>
                'RAX-AUTH:multiFactorEnabled': True/False
                'id': <userid>
                'username': <username>
                'email': <email>
                'enabled': True/False
            }
        }
        '''
        self.log_request(uri, request)
        req_headers = request.headers

        try:
            user_id = KeystoneV2Service.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'
                           .format(user_id))
        except Exception as ex:  #  pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

        if 'x-auth-token' in req_headers:
            try:
                auth_token = req_headers['x-auth-token']
                user_data = self.model.validate_token(auth_token)

                self.log_debug('token {0} maps to tenant {1} and userid {2}'
                               .format(auth_token,
                                       user_data['tenantid'],
                                       user_data['userid']))
            except Exception as ex:
                self.log_exception('bad token lookup')
                return (401, headers, 'Not Authorized')

            try:
                user_info = self.model.get_user_by_id(user_data['tenantid'],
                                                      user_id)

            except:
                self.log_exception('failed to lookup user id {1} under tenant '
                                   'id {0}'
                                   .format(user_data['tenantid'], user_id))
                return (404, headers, 'Not Found')

            data = {
                'user': {
                    'id': user_info['userid'],
                    'name': user_info['username'],
                    'email': user_info['email'],
                    'enabled': user_info['enabled']
                }
            }
            json_data = json.dumps(data)
            return (200, headers, json_data)

        else:
            return (403, headers, 'Forbidden')
