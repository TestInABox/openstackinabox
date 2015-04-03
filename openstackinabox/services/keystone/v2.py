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


class KeystoneV2Errors(Exception):
    pass


class KeystoneV2AuthError(Exception):
    pass


class KeystoneV2AuthForbiddenError(KeystoneV2AuthError):
    pass


class KeystoneV2AuthUnauthorizedError(KeystoneV2AuthError):
    pass


class KeystoneV2Service(BaseService):

    # USER_ID_PATH_REGEX = re.compile('^\/users\/[a-zA-Z]+[\w\.@-]*$')
    USER_ID_PATH_REGEX = re.compile('^\/users\/([0-9]+)$')

    @staticmethod
    def get_user_id_from_path(uri_path):
        uri_matcher = KeystoneV2Service.USER_ID_PATH_REGEX.match(uri_path)
        userid = uri_matcher.groups()[0]
        return userid

    def __init__(self):
        super(KeystoneV2Service, self).__init__('keystone/v2.0')
        self.log_info('initializing keystone v2.0 services...')
        self.__model = KeystoneModel()

        self.register(BaseService.GET,
                      '/tenants',
                      KeystoneV2Service.handle_list_tenants)
        self.register(BaseService.GET,
                      '/users',
                      KeystoneV2Service.handle_list_users)
        self.register(BaseService.POST,
                      '/users',
                      KeystoneV2Service.handle_add_user)
        self.register(BaseService.GET,
                      KeystoneV2Service.USER_ID_PATH_REGEX,
                      KeystoneV2Service.handle_get_user_by_id)
        self.register(BaseService.POST,
                      KeystoneV2Service.USER_ID_PATH_REGEX,
                      KeystoneV2Service.handle_update_user_by_id)
        self.log_info('initialized')

    @property
    def model(self):
        return self.__model

    @model.setter
    def model(self, value):
        if isinstance(value, KeystoneModel):
            self.__model = value
        else:
            raise TypeError('model is not an instance of KeystoneModel')

    def helper_validate_token(self, request_headers,
                              enforce_admin, service_admin):
        if 'x-auth-token' not in request_headers:
            raise KeystoneV2AuthForbiddenError('no auth token')

        try:
            auth_token = request_headers['x-auth-token']
            user_data = None
            if service_admin:
                user_data = self.model.validate_token_service_admin(auth_token)

            elif enforce_admin:
                user_data = self.model.validate_token_admin(auth_token)

            else:
                user_data = self.model.validate_token(auth_token)

            self.log_debug('token {0} maps to tenant {1} and userid {2}'
                           .format(auth_token,
                                   user_data['tenantid'],
                                   user_data['userid']))
        except Exception as ex:
            raise KeystoneV2AuthUnauthorizedError(
                'invalid or expired auth token')

        return user_data

    def helper_authenticate(self, request_headers, headers,
                            enforce_admin, service_admin):

        try:
            user_data = self.helper_validate_token(request_headers,
                                                   enforce_admin,
                                                   service_admin)

        except KeystoneV2AuthForbiddenError:
            self.log_exception('no token')
            return (403, headers, 'Forbidden')

        except KeystoneV2AuthUnauthorizedError:
            self.log_exception('invalid or expired token')
            return (401, headers, 'Not Authorized')

        return user_data

    def handle_list_tenants(self, request, uri, headers):
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
        req_headers = request.headers

        user_data = self.helper_authenticate(req_headers, headers, True, True)
        if isinstance(user_data, tuple):
            return user_data

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

    def handle_list_users(self, request, uri, headers):
        req_headers = request.headers
        '''
        '''
        self.log_request(uri, request)

        user_data = self.helper_authenticate(req_headers, headers, True, False)
        if isinstance(user_data, tuple):
            return user_data

        def user_data_filter(user):
            self.log_debug('Filtering data on {0}'.format(user))
            return {
                'id': user['userid'],
                'enabled': user['enabled'],
                'username': user['username'],
                'email': user['email'],
            }

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

    def handle_add_user(self, request, uri, headers):
        '''
        201 -> created
        400 -> Bad Request - missing one or more element, or values were
                             invalid
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

        user_data = self.helper_authenticate(req_headers, headers, True, False)
        if isinstance(user_data, tuple):
            return user_data

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

        user_data = self.helper_authenticate(req_headers,
                                             headers,
                                             False,
                                             False)
        if isinstance(user_data, tuple):
            return user_data

        try:
            user_id = KeystoneV2Service.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'
                           .format(user_id))

        except Exception as ex:  # pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

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

    def handle_update_user_by_id(self, request, uri, headers):
        '''
        200 -> OK
        400 -> Bad Request
        401 -> Unauthorized
        403 -> Forbidden
        404 -> Not Found
        405 -> Invalid Method
        413 -> Over Limit
        415 -> Bad Media Type
        503 -> Server Fault
        '''
        self.log_request(uri, request)
        req_headers = request.headers

        user_data = self.helper_authenticate(req_headers,
                                             headers,
                                             False,
                                             False)
        if isinstance(user_data, tuple):
            return user_data

        try:
            user_id = KeystoneV2Service.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'
                           .format(user_id))

        except Exception as ex:  # pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

        req_body = request.body.decode('utf-8')
        json_data = json.loads(req_body)

        if 'user' not in json_data:
            return (400, headers, 'bad request')

        if 'id' not in json_data['user'] or\
                'username' not in json_data['user']:
            return (400, headers, 'bad request')

        try:
            user_info = self.model.get_user_by_id(user_data['tenantid'],
                                                  user_id)
        except Exception as ex:
            self.log_exception('failed to get user data')
            return (404, headers, 'Not Found')

        if 'enabled' in json_data['user']:
            user_info['enabled'] = json_data['user']['enabled']

        if 'email' in json_data['user']:
            user_info['email'] = json_data['user']['email']

        if 'OS-KSADM:password' in json_data['user']:
            user_info['password'] = json_data['user']['OS-KSADM:password']

        try:
            self.model.update_user_by_user_id(tenantid=user_data['tenantid'],
                                              userid=user_id,
                                              email=user_info['email'],
                                              password=user_info['password'],
                                              apikey=user_info['apikey'],
                                              enabled=user_info['enabled'])
        except Exception as ex:  # pragma: no cover
            self.log_exception('failed to update user')
            return (503, headers, 'Server error')

        return (200, headers, json.dumps(user_info))
