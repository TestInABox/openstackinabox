"""
OpenStack Keystone Model
"""
import copy
import sqlite3

import six

from openstackinabox.models import base_model
from openstackinabox.models.keystone import exceptions

from openstackinabox.models.keystone.db.endpoints import (
    KeystoneDbServiceEndpoints
)
from openstackinabox.models.keystone.db.roles import KeystoneDbRoles
from openstackinabox.models.keystone.db.services import KeystoneDbServices
from openstackinabox.models.keystone.db.tenants import KeystoneDbTenants
from openstackinabox.models.keystone.db.tokens import KeystoneDbTokens
from openstackinabox.models.keystone.db.users import KeystoneDbUsers


"""
    - Build a service catalog
    - Add tenants
    - Add services
    - Add roles
    - Authentication

    POST /v2.0/users

    POST /v2.0/tokens/
    DELETE /v2.0/tokens/{token}
    GET /v2.0/tentants{?name}
"""

schema = [
    '''
        CREATE TABLE keystone_tenants
        (
            tenantid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            enabled INTEGER DEFAULT 1
        )
    ''',
    '''
        CREATE TABLE keystone_users
        (
            tenantid INTEGER NOT NULL REFERENCES keystone_tenants(tenantid),
            userid INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT,
            apikey TEXT,
            enabled INTEGER DEFAULT 1
        )
    ''',
    '''
        CREATE TABLE keystone_tokens
        (
            tenantid INTEGER NOT NULL REFERENCES keystone_tenants(tenantid),
            userid INTEGER NOT NULL REFERENCES keystone_users(userid),
            token TEXT NOT NULL UNIQUE,
            ttl DATETIME NOT NULL,
            revoked INTEGER DEFAULT 0
        )
    ''',
    '''
        CREATE TABLE keystone_roles
        (
            roleid INTEGER PRIMARY KEY AUTOINCREMENT,
            rolename TEXT NOT NULL UNIQUE
        )
    ''',
    '''
        CREATE TABLE keystone_user_roles
        (
            tenantid INTEGER NOT NULL REFERENCES keystone_tenants(tenantid),
            userid INTEGER NOT NULL REFERENCES keystone_users(userid),
            roleid INTEGER NOT NULL REFERENCES keystone_roles(roleid)
        )
    ''',
    '''
        CREATE TABLE keystone_services
        (
            serviceid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL
        )
    ''',
    '''
        CREATE TABLE keystone_service_endpoints
        (
            serviceid INTEGER NOT NULL REFERENCES keystone_services(serviceid),
            endpointid INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            versionInfo TEXT,
            versionList TEXT,
            versionId TEXT
        )
    ''',
    '''
        CREATE TABLE keystone_service_endpoints_url
        (
            endpointid INTEGER NOT NULL REFERENCES
                keystone_service_endpoints(endpointid),
            urlid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )
    '''
]

SQL_ADD_END_POINT = '''
    INSERT INTO keystone_service_endpoints
    (serviceid, region, versionInfo, versionlist, versionId)
    VALUES(:serviceid, :region, :versioninfo, :versionlist, :versionid)
'''


class KeystoneModel(base_model.BaseModel):

    CHILD_MODELS = {
        'roles': KeystoneDbRoles,
        'services': KeystoneDbServices,
        'endpoints': KeystoneDbServiceEndpoints,
        'tenants': KeystoneDbTenants,
        'tokens': KeystoneDbTokens,
        'users': KeystoneDbUsers
    }

    @staticmethod
    def initialize_db_schema(db_instance):
        dbcursor = db_instance.cursor()
        for table_sql in schema:
            dbcursor.execute(table_sql)
        db_instance.commit()

    @classmethod
    def get_child_models(cls, instance, db_instance):
        return {
            model_name: model_type(instance, db_instance)
            for model_name, model_type in six.iteritems(cls.CHILD_MODELS)
        }

    def __init__(self, initialize=True):
        super(KeystoneModel, self).__init__('KeystoneModel')
        self.database = sqlite3.connect(':memory:')
        self.child_models = self.get_child_models(self, self.database)
        if initialize:
            self.init_database()

    @property
    def users(self):
        return self.child_models['users']

    @property
    def tenants(self):
        return self.child_models['tenants']

    @property
    def tokens(self):
        return self.child_models['tokens']

    @property
    def roles(self):
        return self.child_models['roles']

    @property
    def services(self):
        return self.child_models['services']

    @property
    def endpoints(self):
        return self.child_models['endpoints']

    def init_database(self):
        self.log_info('Initializing database')
        self.initialize_db_schema(self.database)

        self.services.initialize()
        self.tokens.initialize()
        self.roles.initialize()
        self.tenants.initialize()
        self.users.initialize()

        self.tokens.add(
            tenant_id=self.tenants.admin_tenant_id,
            user_id=self.users.admin_user_id,
            token=self.tokens.admin_token
        )

        self.database.commit()
        self.log_info('Database initialized')

    def validate_token_admin(self, token):
        try:
            self.log_debug('Checking token {0} for registration...'
                           .format(token))
            user_data = self.tokens.validate_token(token)

            self.log_debug('Token is valid.')
            self.log_debug(
                'Accessing user credentials for {0}/{1}...'.format(
                    user_data['tenantid'],
                    user_data['userid']
                )
            )
            user_roles = self.roles.get_user_roles(
                user_data['tenantid'],
                user_data['userid']
            )
            self.log_debug('User has {0} roles...'.format(len(user_roles)))
            for role_data in user_roles:
                roleid = role_data['id']
                rolename = role_data['name']
                self.log_debug(
                    'Checking against role {0} - {1}'.format(
                        roleid,
                        rolename
                    )
                )
                if rolename == self.roles.IDENTITY_ADMIN_ROLE:
                    self.log_debug(
                        'User has {0} role'.format(
                            self.roles.IDENTITY_ADMIN_ROLE
                        )
                    )
                    return user_data

        except Exception as ex:
            self.log_exception('Error: {0}'.format(ex))

        raise exceptions.KeystoneInvalidTokenError('Invalid Token')

    def validate_token_service_admin(self, token):
        try:
            self.log_debug('Checking token {0} for validity...'.format(token))
            user_data = self.validate_token_admin(token)

            self.log_debug(
                'Checking if token {0} is the sole service admin '
                'token...'.format(
                    token
                )
            )

            if token == self.tokens.admin_token:
                self.log_debug('Token {0} validated.'.format(token))
                return user_data

        except Exception as ex:
            self.log_exception('Error: {0}'.format(ex))

        raise exceptions.KeystoneInvalidTokenError(
            'Not the service admin token'
        )

    def get_auth_token_entry(self, token_data, user_data):
        # build the 'auth' section of the service catalog
        return {
            'id': token_data['token'],
            'expires': token_data['expires'],
            'tenant': {
                'id': user_data['tenant_id'],
                'name': user_data['username']
                # 'RAX-AUTH:authenticatedBy': [
                #    None
                # ]
            }
        }

    def get_auth_user_entry(self, user_data):
        return {
            'id': user_data['user_id'],
            'roles': [
                {
                    'id': role['id'],
                    # 'serviceId': None,
                    # 'description': None,
                    'name': role['name']
                }
                for role in self.roles.get_user_roles(
                    tenant_id=user_data['tenant_id'],
                    user_id=user_data['user_id']
                )
            ],
            'name': user_data['username'],
            # 'RAX-AUTH:defaultRegion': None
        }

    def get_auth_service_catalog(self, user_data):
        # build the services section of the service catalog
        def get_endpoints_for_service(service_id):
            def insert_if_not_none(dest, dest_key, source, source_key):
                for i in [dest, dest_key, source, source_key]:
                    print("param: {0}".format(i))
                dest[dest_key] = source[source_key]

            optional_keys = [
                {'source': 'region', 'dest': 'region'},
                {'source': 'version_info', 'dest': 'versionInfo'},
                {'source': 'version_list', 'dest': 'versionList'},
                {'source': 'version_id', 'dest': 'versionId'},
            ]

            for endpoint_data in self.endpoints.get(service_id):
                endpoint_info = {
                    'tenantId': None,
                }

                for key_copy in optional_keys:
                    insert_if_not_none(
                        endpoint_info,
                        key_copy['dest'],
                        endpoint_data,
                        key_copy['source']
                    )

                for url_data in self.endpoints.get_url(
                    endpoint_data['endpoint_id']
                ):
                    endpoint_info[url_data['name']] = (
                        url_data['url']
                    )

                yield endpoint_info

        return [
            {
                'name': service_data['name'],
                'endpoints': [
                    endpoint_data
                    for endpoint_data
                    in get_endpoints_for_service(service_data['id'])
                ],
                'type': service_data['type']
            }
            for service_data in self.services.get()
        ]

    def get_service_catalog(self, token, user):
        return {
            'serviceCatalog': self.get_auth_service_catalog(user),
            'token': self.get_auth_token_entry(token, user),
            'user': self.get_auth_user_entry(user)
        }

    def password_authenticate(self, password_data):
        if not self.users.validate_username(password_data['username']):
            self.log_error('Username Validation Failed')
            raise exceptions.KeystoneUserError('Invalid User Data - Username')

        if not self.users.validate_password(password_data['password']):
            self.log_error('Password Validation Failed')
            raise exceptions.KeystoneUserError('Invalid User Data - Password')

        user = None
        user_counter = 0
        for user_data in self.users.get_by_name_or_tenant_id(
            username=password_data['username']
        ):
            user_counter = user_counter + 1
            if user_data['password'] == password_data['password']:
                user = user_data
                break

        if user is None:
            if user_counter:
                raise exceptions.KeystoneUserInvalidPasswordError(
                    'Bad Password'
                )

            else:
                raise exceptions.KeystoneUnknownUserError(
                    'Unable to locate user'
                )

        if user['enabled'] is False:
            raise exceptions.KeystoneDisabledUserError('User is disabled')

        self.tokens.add(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
        )

        token = self.tokens.get_by_user_id(
            user['user_id']
        )

        return self.get_service_catalog(token, user)

    def apikey_authenticate(self, apikey_data):
        if not self.users.validate_username(apikey_data['username']):
            self.log_error('Username Validation Failed')
            raise exceptions.KeystoneUserError('Invalid User Data - Username')

        if not self.users.validate_apikey(apikey_data['apiKey']):
            self.log_error('API Key Validation Failed')
            raise exceptions.KeystoneUserError('Invalid User Data - API Key')

        user = None
        user_counter = 0
        for user_data in self.users.get_by_name_or_tenant_id(
            username=apikey_data['username']
        ):
            user_counter = user_counter + 1
            if user_data['apikey'] == apikey_data['apiKey']:
                user = user_data
                break

        if user is None:
            if user_counter:
                raise exceptions.KeystoneUserInvalidApiKeyError('Bad API Key')

            else:
                raise exceptions.KeystoneUnknownUserError(
                    'Unable to locate user'
                )

        if user['enabled'] is False:
            raise exceptions.KeystoneDisabledUserError(
                'User is disabled'
            )

        self.tokens.add(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
        )

        token = self.tokens.get_by_user_id(
            user['user_id']
        )

        return self.get_service_catalog(token, user)

    def tenant_id_token_auth(self, auth_data):
        try:
            tenant_id = auth_data['tenantId']
            token = auth_data['token']['id']
        except KeyError as ex:
            raise exceptions.KeystoneUserError(
                'Invalid user Data - {0}'.format(ex)
            )

        if not self.tenants.validate_tenant_id(tenant_id):
            self.log_error('Username Validation Failed')
            raise exceptions.KeystoneUserError('Invalid User Data - Username')

        token_data = self.tokens.validate_token(token)

        tenant_data = self.tenants.get_by_id(tenant_id=tenant_id)
        if not tenant_data['enabled']:
            raise exceptions.KeystoneTenantError('Tenant is disabled')

        user = None
        user_counter = 0
        for user_data in self.users.get_by_name_or_tenant_id(
            tenant_id=tenant_id
        ):
            user_counter = user_counter + 1
            if user_data['user_id'] == token_data['userid']:
                user = user_data

        if user is None:
            raise exceptions.KeystoneUnknownUserError('Unable to locate user')

        if user['enabled'] is False:
            raise exceptions.KeystoneDisabledUserError('User is disabled')

        # side-effects if token revoked or expired
        self.tokens.check_expiration(token_data)

        return self.get_service_catalog(token_data, user)

    def tenant_name_token_auth(self, auth_data):
        try:
            tenant_name = auth_data['tenantName']
            auth_data['token']['id']
        except KeyError as ex:
            raise exceptions.KeystoneUserError(
                'Invalid user Data - {0}'.format(ex)
            )

        if not self.tenants.validate_tenant_name(tenant_name):
            self.log_error('Tenant Name Validation Failed')
            raise exceptions.KeystoneUserError(
                'Invalid User Data - Tenant Name'
            )

        tenant_data = self.tenants.get_by_name(tenant_name=tenant_name)

        new_auth_data = copy.deepcopy(auth_data)
        new_auth_data['tenantId'] = tenant_data['id']

        return self.tenant_id_token_auth(new_auth_data)
