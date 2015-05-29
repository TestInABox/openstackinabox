"""
OpenStack Keystone v2 Service - Users - by user id
"""
import json
import re

import six
from six.moves.urllib import parse

from openstackinabox.services.base_service import BaseService
from openstackinabox.services.base_subservice import BaseSubService


class Keystonev2ServiceUsersById(BaseSubService):

    USER_ID_REGEX = '([0-9]+)'

    PATH = '/users/{0}'.format(USER_ID_REGEX)

    # USER_ID_PATH_REGEX = re.compile('^\/users\/[a-zA-Z]+[\w\.@-]*$')
    PATH_REGEX = re.compile('^\/users\/{0}$'
                            .format(USER_ID_REGEX))
    ROUTE_REGEX = re.compile('^\/users\/{0}'
                             .format(USER_ID_REGEX))

    USER_ID_KSADM_CREDENTIAL_PATH_REGEX = re.compile(
        '^\/users\/{0}/OS-KSADM/credentials$'
        .format(USER_ID_REGEX))

    @staticmethod
    def get_user_id_from_path(uri_path):
        uri_matcher = None

        regexes = [
            Keystonev2ServiceUsersById.PATH_REGEX,
            Keystonev2ServiceUsersById.USER_ID_KSADM_CREDENTIAL_PATH_REGEX,
        ]

        for r in regexes:
            uri_matcher = r.match(uri_path)
            if uri_matcher is not None:
                break

        userid = uri_matcher.groups()[0]
        return userid

    def get_route_regex(self):
        return Keystonev2ServiceUsersById.ROUTE_REGEX

    def __init__(self, parent):
        super(Keystonev2ServiceUsersById, self).__init__('usersbyid', parent)

        self.register(BaseService.GET,
                      Keystonev2ServiceUsersById.PATH_REGEX,
                      Keystonev2ServiceUsersById.handle_get_user_by_id)
        self.register(BaseService.POST,
                      Keystonev2ServiceUsersById.PATH_REGEX,
                      Keystonev2ServiceUsersById.handle_update_user_by_id)
        self.register(BaseService.DELETE,
                      Keystonev2ServiceUsersById.PATH_REGEX,
                      Keystonev2ServiceUsersById.handle_delete_user_by_id)

        # To be moved still
        self.register(BaseService.POST,
                      Keystonev2ServiceUsersById.USER_ID_KSADM_CREDENTIAL_PATH_REGEX,
                      Keystonev2ServiceUsersById.handle_add_credentials_to_user)

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

        user_data = self.get_root().helper_authenticate(req_headers,
                                                        headers,
                                                        False,
                                                        False)
        if isinstance(user_data, tuple):
            return user_data

        try:
            user_id = Keystonev2ServiceUsersById.get_user_id_from_path(uri)
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

        user_data = self.get_root().helper_authenticate(req_headers,
                                                        headers,
                                                        False,
                                                        False)
        if isinstance(user_data, tuple):
            return user_data

        try:
            user_id = Keystonev2ServiceUsersById.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'
                           .format(user_id))

        except Exception as ex:  # pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

        req_body = request.body.decode('utf-8') if hasattr(
            request.body, 'decode') else request.body
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

    def handle_delete_user_by_id(self, request, uri, headers):
        '''
        204 -> OK
        400 -> Bad Request
        401 -> Unauthorized
        403 -> Forbidden
        404 -> Not Found
        405 -> Invalid Method
        413 -> Over Limit
        503 -> Server Fault
        '''
        self.log_request(uri, request)
        req_headers = request.headers

        user_data = self.get_root().helper_authenticate(req_headers,
                                                        headers,
                                                        False,
                                                        False)
        if isinstance(user_data, tuple):
            return user_data

        try:
            user_id = Keystonev2ServiceUsersById.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'
                           .format(user_id))

        except Exception as ex:  # pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

        try:
            user_info = self.model.get_user_by_id(user_data['tenantid'],
                                                  user_id)
        except Exception as ex:
            self.log_exception('failed to get user data')
            return (404, headers, 'Not Found')

        try:
            self.model.delete_user(tenantid=user_data['tenantid'],
                                   userid=user_id)

        except Exception as ex:  # pragma: no cover
            self.log_exception('failed to delete user')
            return (503, headers, 'Server error')

        return (204, headers, '')

    """
    To be moved still
    """

    def handle_add_credentials_to_user(self, request, uri, headers):
        '''
        201 -> Created
        400 -> Bad Request
        403 -> Forbidden
        404 -> Not Found
        405 -> Invalid Method
        413 -> Over Limit
        415 -> Bad Media Type
        503 -> Service Fault
        '''
        self.log_request(uri, request)
        req_headers = request.headers

        user_data = self.get_root().helper_authenticate(req_headers,
                                                        headers,
                                                        True,
                                                        False)
        if isinstance(user_data, tuple):
            return user_data

        req_body = request.body.decode('utf-8') if hasattr(
            request.body, 'decode') else request.body
        json_data = json.loads(req_body)

        try:
            password_data = json_data['passwordCredentials']

        except LookupError:
            self.log_exception('invalid request')
            return (400, headers, 'bad request')

        try:
            user_id = Keystonev2ServiceUsersById.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'
                           .format(user_id))

        except Exception as ex:  # pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

        try:
            user_info = self.model.get_user_by_id(user_data['tenantid'],
                                                  user_id)
        except:
            self.log_exception('failed to get user data')
            return (404, headers, 'Not found')

        for k, v in six.iteritems(password_data):
            if k in ('username', 'email', 'password', 'apikey'):
                user_info[k] = v
            else:
                self.log_debug('invalid update parameter {0}'.format(k))

        try:
            self.model.update_user_by_user_id(user_info['tenantid'],
                                              user_info['userid'],
                                              user_info['email'],
                                              user_info['password'],
                                              user_info['apikey'],
                                              user_info['enabled'])

        except Exception as ex:  # pragma: no cover
            self.log_exception('failed to update user')
            return (503, headers, 'Server error')

        return (201, headers, '')
