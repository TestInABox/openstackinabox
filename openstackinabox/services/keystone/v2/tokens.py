import json

from openstackinabox.services.base_service import BaseService
from openstackinabox.services.keystone.v2.base import KeystoneV2ServiceBase
from openstackinabox.services.keystone.v2 import exceptions


class KeystoneV2ServiceTokens(KeystoneV2ServiceBase):

    def __init__(self, model):
        super(KeystoneV2ServiceTokens, self).__init__('keystone/v2.0/tokens')
        self.model = model

        self.register(
            BaseService.POST,
            '/tokens',
            KeystoneV2ServiceTokens.handle_authenticate
        )

    def handle_authenticate(self, request, uri, headers):
        '''
        POST /tokens

        Headers:

        Body: one of the following
            1. user + password
                {
                    'auth': {
                        'passwordCredentials': {
                            'username': None,
                            'password': None
                        }
                    }
                }
            2. user + apikey
                {
                    'auth': {
                        'RAX-KSKEY:apiKeyCredentials': {
                            'username': None,
                            'apiKey': None
                        }
                    }
                }
            3. tenant-id + apikey
                {
                    'auth': {
                        'RAX-KSKEY:apiKeyCredentials': {
                            'username': None,
                            'apiKey': None
                        }
                        'tenantId': None
                        'tenantName': None
                    }
                }
            4. tenant-id + token
                {
                    'auth': {
                        'tenantId': None,
                        'token': {
                            'id': None
                        }
                    }
                }
            5. tenant-name + token
                {
                    'auth': {
                        'tenantName': None,
                        'token': {
                            'id': None
                        }
                    }
                }

        200 -> OK + JSON Body w/ Service Catalog
        400 -> Bad Request: one or more required parameters
                            are missing or invalid
        401 -> not authorized
        403 -> forbidden (no permission)
        404 -> Not found
        500 -> Service Fault
        '''
        self.log_request(uri, request)
        req_body = request.body

        body = json.loads(req_body)
        if 'auth' not in body:
            return (400, headers, "Invalid request")

        auth_data = body['auth']
        user_data = None
        try:
            if 'passwordCredentials' in auth_data:
                user_data = self.model.password_authenticate(
                    auth_data['passwordCredentials']
                )
            elif 'RAX-KSKEY:apiKeyCredentials' in auth_data:
                user_data = self.model.apikey_authenticate(
                    auth_data['RAX-KSKEY:apiKeyCredentials']
                )
            elif 'tenantId' in auth_data:
                user_data = self.model.tenant_id_token_auth(
                    auth_data
                )
            elif 'tenantName' in auth_data:
                user_data = self.model.tenant_name_token_auth(
                    auth_data
                )
            else:
                return (400, headers, "Invalid request")

            response_body = {
                'access': user_data
            }
            return (200, headers, json.dumps(response_body))

        except exceptions.KeystoneUserInvalidPasswordError:
            return (401, headers, "Not Authorized")

        except exceptions.KeystoneUserInvalidApiKeyError:
            return (401, headers, "Not Authorized")

        except exceptions.KeystoneTokenError:
            return (401, headers, "Not Authorized")

        except exceptions.KeystoneTenantError:
            return (403, headers, "Access Forbidden")

        except exceptions.KeystoneDisabledUserError:
            return (403, headers, "Access Forbidden")

        except exceptions.KeystoneUnknownUserError:
            return (404, headers, "Not Found")

        except exceptions.KeystoneUserError as ex:
            self.log_error('Invalid Data - {0}'.format(ex))
            return (400, headers, "Invalid request")

    """
    def handle_validate_token(self, request, uri, headers):
        '''
        GET /tokens/<token>

        Headers:
            X-Auth-Token
            belongsTo (optional) - token must belong to the specified tenant

        Body:
            None

        200 -> OK
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

        " " "
        Standard Response
        response_body = {
            'access': {
                'token': {
                    'id': None,
                    'expires': None,
                    'tenant': {
                        'id': None,
                        'name': None
                    }
                    'RAX-AUTH:authenticatedBy': [
                        None
                    ]
                },
                'user': {
                    'id': None,
                    'roles': [
                        {
                            'id': None,
                            'serviceId': None,
                            'description': None,
                            'name': "None"
                        }
                    ],
                    'name': None,
                    'RAX-AUTH:defaultRegion': None
                }
            }
        }

        Impersonation Response
        response_body = {
            'access': {
                'token': {
                    'id': None,
                    'expires': None,
                    'tenant': {
                        'id': None,
                        'name': None,
                    }
                },
                'user': {
                    'id': None,
                    'roles': [
                        {
                            'id': None,
                            'serviceId': None,
                            'description': None,
                            'name': "None"
                        }
                    ],
                    'name': None,
                },
                'RAX-AUTH:impersonator': {
                    'id': None,
                    'name': None,
                    'roles': [
                        {
                            'id': None,
                            'name': "<Racker>"
                        },
                        {
                            'id': None,
                            'name': "None"
                        }
                    ]
                }
            }
        }

        Racker Response
        response_body = {
            'access': {
                'token': {
                    'expired': None,
                    'id': None
                }
            },
            'user': {
                'RAX-Auth:defaultRegion': None,
                'roles': [
                    {
                        'id': None,
                        'serviceId': None,
                        'description': None,
                        'name': "None"
                    }
                ],
                'id': None
            }
        }
        " " "
        return (503, headers, "Implementation Stub")

    def handle_revoke_token(self, request, uri, headers):
        '''
        DELETE /tokens

        Headers:
            X-Auth-Token

        Body:
            None

        204 -> OK
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
            # TODO(BenjamenMeyer): Delete/Invalidate the token
            return (204, headers, None)

        return (503, headers, "Implementation Stub")
    """
