"""
OpenStack Keystone v2 Service - Users
"""
import json
import re

import six
from six.moves.urllib import parse

from openstackinabox.services.base_service import BaseService
from openstackinabox.services.base_subservice import BaseSubService
from openstackinabox.services.keystone.v2.users.byuserid import (
    Keystonev2ServiceUsersById
)


class KeystoneV2ServiceUsers(BaseSubService):

    PATH = '/users'
    ROUTE_REGEX = re.compile('^{0}'.format(PATH))
    PATH_REGEX = re.compile('^{0}$'.format(PATH))

    def __init__(self, parent):
        super(KeystoneV2ServiceUsers, self).__init__('users', parent)
        self.register(BaseService.GET,
                      KeystoneV2ServiceUsers.PATH,
                      KeystoneV2ServiceUsers.handle_list_users)
        self.register(BaseService.POST,
                      KeystoneV2ServiceUsers.PATH,
                      KeystoneV2ServiceUsers.handle_add_user)

        self.__subservices = [
            Keystonev2ServiceUsersById(self)
        ]
        self.add_subservices(self.__subservices)

    def get_route_regex(self):
        return KeystoneV2ServiceUsers.ROUTE_REGEX

    def handle_list_users(self, request, uri, headers):
        req_headers = request.headers
        '''
        '''
        self.log_request(uri, request)

        user_data = self.get_root().helper_authenticate(req_headers,
                                                        headers,
                                                        True,
                                                        False)
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

        user_data = self.get_root().helper_authenticate(req_headers,
                                                        headers,
                                                        True,
                                                        False)
        if isinstance(user_data, tuple):
            return user_data

        current_user = self.model.get_user_by_id(user_data['tenantid'],
                                                 user_data['userid'])

        req_body = request.body.decode('utf-8') if hasattr(
            request.body, 'decode') else request.body
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

            return (201, headers, '')

        except Exception as ex:
            self.log_exception('User Add Failure')
            # is 404 correct?
            return (404, headers, 'failed to add user')
