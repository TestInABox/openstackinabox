import json

import six
from six.moves.urllib import parse

from openstackinabox.services.base_service import BaseService
from openstackinabox.services.keystone.v2.base import KeystoneV2ServiceBase


class KeystoneV2ServiceUsers(KeystoneV2ServiceBase):

    def __init__(self, model):
        super(KeystoneV2ServiceUsers, self).__init__('keystone/v2.0/users')
        self.model = model

        self.register(BaseService.GET,
                      '/users',
                      KeystoneV2ServiceUsers.handle_list_users)
        self.register(BaseService.POST,
                      '/users',
                      KeystoneV2ServiceUsers.handle_add_user)
        self.register(BaseService.GET,
                      KeystoneV2ServiceUsers.USER_ID_PATH_REGEX,
                      KeystoneV2ServiceUsers.handle_get_user_by_id)
        self.register(BaseService.POST,
                      KeystoneV2ServiceUsers.USER_ID_PATH_REGEX,
                      KeystoneV2ServiceUsers.handle_update_user_by_id)
        self.register(BaseService.DELETE,
                      KeystoneV2ServiceUsers.USER_ID_PATH_REGEX,
                      KeystoneV2ServiceUsers.handle_delete_user_by_id)
        self.register(
            BaseService.POST,
            KeystoneV2ServiceUsers.USER_ID_KSADM_CREDENTIAL_PATH_REGEX,
            KeystoneV2ServiceUsers.handle_add_credentials_to_user
        )

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
                'id': user['user_id'],
                'enabled': user['enabled'],
                'username': user['username'],
                'email': user['email'],
            }

        parsed_uri = parse.urlparse(uri)
        query = parsed_uri.query

        if len(query) > 0:
            query_data = parse.parse_qs(query)

            if 'name' in query_data:
                user_info = self.model.users.get_by_name(
                    tenant_id=user_data['tenantid'],
                    username=query_data['name'][0]
                )
                response_body = {
                    'user': user_data_filter(user_info)
                }
                return (200, headers, json.dumps(response_body))

        response_body = {
            'users': [
                user_data_filter(user_info)
                for user_info in
                self.model.users.get_for_tenant_id(
                    user_data['tenantid']
                )
            ]
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

        current_user = self.model.users.get_by_id(
            tenant_id=user_data['tenantid'],
            user_id=user_data['userid']
        )

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

        if not self.model.users.validate_username(username):
            self.log_debug('username invalid')
            return (400, headers, 'bad request')

        try:
            password = json_data['user']['OS-KSADM:password']
        except LookupError:
            password = None

        if password is not None:
            if not self.model.users.validate_password(password):
                self.log_debug('invalid password')
                return (400, headers, 'bad request')

        try:
            self.model.users.add(
                tenant_id=current_user['tenant_id'],
                username=username,
                email=email,
                password=password,
                enabled=enabled
            )

            return (201, headers, '')

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
            user_id = KeystoneV2ServiceUsers.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'
                           .format(user_id))

        except Exception as ex:  # pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

        try:
            user_info = self.model.users.get_by_id(
                tenant_id=user_data['tenantid'],
                user_id=user_id
            )

        except:
            self.log_exception(
                'failed to lookup user id {1} under tenant id {0}'.format(
                    user_data['tenantid'],
                    user_id
                )
            )
            return (404, headers, 'Not Found')

        data = {
            'user': {
                'id': user_info['user_id'],
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
            user_id = KeystoneV2ServiceUsers.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'.format(user_id))

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
            user_info = self.model.users.get_by_id(
                tenant_id=user_data['tenantid'],
                user_id=user_id
            )
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
            self.model.users.update_by_id(
                tenant_id=user_data['tenantid'],
                user_id=user_id,
                email=user_info['email'],
                password=user_info['password'],
                apikey=user_info['apikey'],
                enabled=user_info['enabled']
            )
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

        user_data = self.helper_authenticate(req_headers,
                                             headers,
                                             False,
                                             False)
        if isinstance(user_data, tuple):
            return user_data

        try:
            user_id = KeystoneV2ServiceUsers.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'
                           .format(user_id))

        except Exception as ex:  # pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

        try:
            self.model.users.get_by_id(
                tenant_id=user_data['tenantid'],
                user_id=user_id
            )
        except Exception as ex:
            self.log_exception('failed to get user data')
            return (404, headers, 'Not Found')

        try:
            self.model.users.delete(
                tenant_id=user_data['tenantid'],
                user_id=user_id
            )

        except Exception as ex:  # pragma: no cover
            self.log_exception('failed to delete user')
            return (503, headers, 'Server error')

        return (204, headers, '')

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

        user_data = self.helper_authenticate(req_headers,
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
            user_id = KeystoneV2ServiceUsers.get_user_id_from_path(uri)
            self.log_debug('Lookup of user id {0} requested'.format(user_id))

        except Exception as ex:  # pragma: no cover
            self.log_exception('Failed to get user id from path')
            return (400, headers, 'bad request')

        try:
            user_info = self.model.users.get_by_id(
                tenant_id=user_data['tenantid'],
                user_id=user_id
            )
        except:
            self.log_exception('failed to get user data')
            return (404, headers, 'Not found')

        for k, v in six.iteritems(password_data):
            if k in ('username', 'email', 'password', 'apikey'):
                user_info[k] = v
            else:
                self.log_debug('invalid update parameter {0}'.format(k))

        try:
            self.model.users.update_by_id(
                tenant_id=user_info['tenant_id'],
                user_id=user_info['user_id'],
                email=user_info['email'],
                password=user_info['password'],
                apikey=user_info['apikey'],
                enabled=user_info['enabled']
            )

        except Exception as ex:  # pragma: no cover
            self.log_exception('failed to update user')
            return (503, headers, 'Server error')

        return (201, headers, '')
