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
    """
    Keystone Model

    :ivar sqlite3 database: sqlite3 database used for the data store
    :ivar iterable child_models: iterable containing the child models
    """

    # child models for easier maintenance
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
        """
        Initialize the db instance

        :param sqlite3 db_instance: SQLite3 DB instance to use for the model
            data storage
        """
        dbcursor = db_instance.cursor()
        for table_sql in schema:
            dbcursor.execute(table_sql)
        db_instance.commit()

    @classmethod
    def get_child_models(cls, instance, db_instance):
        """
        Retrieve the child models

        :param obj instance: instance to use as the master model for the
            child model
        :param sqlite3 db_instance: SQLite3 db to provide the child models
            for their data storage
        :retval: iterable with all the child models instantiated
        """
        return {
            model_name: model_type(instance, db_instance)
            for model_name, model_type in six.iteritems(cls.CHILD_MODELS)
        }

    def __init__(self, initialize=True):
        """
        :param boolean initialize: whether or not to initialize the database
            on object instantiation
        """
        super(KeystoneModel, self).__init__('KeystoneModel')
        self.database = sqlite3.connect(':memory:')
        self.child_models = self.get_child_models(self, self.database)
        if initialize:
            self.init_database()

    @property
    def users(self):
        """
        Access the user model
        """
        return self.child_models['users']

    @property
    def tenants(self):
        """
        Access the tenant model
        """
        return self.child_models['tenants']

    @property
    def tokens(self):
        """
        Access the token model
        """
        return self.child_models['tokens']

    @property
    def roles(self):
        """
        Access the role model
        """
        return self.child_models['roles']

    @property
    def services(self):
        """
        Access the service catalog model
        """
        return self.child_models['services']

    @property
    def endpoints(self):
        """
        Access the service endpoint model
        """
        return self.child_models['endpoints']

    def init_database(self):
        """
        Initialize the database

        .. note:: This also ends up initializing the built-in admin auth
            functionality and setting up the Admin account and token.
        """
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
        """
        Validate the incoming token as an admin token

        :param unicode token: user specified token to validate
        :retval: dict containing the user data
        :raises: KeystoneInvalidTokenError if the token is invalid
            or there are any other errors during the token lookup
        """
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
        """
        Validate the incoming token as an admin token and it is the special
        internally generated service admin token.

        :param unicode token: user specified token to validate
        :retval: dict containing the user data
        :raises: KeystoneInvalidTokenError if the token is invalid
            or there are any other errors during the token lookup
        """
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
        """
        Build the `auth` section of the service catalog

        :param dict token_data: dict containing the token data
        :param dict user_data: dict containing the user data
        :retval: dict containing the auth section of the service catalog
        """
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
        """
        Build the `user` section of the service catalog

        :param dict user_data: dict containing the user data
        :retval: dict contianing the user section of the service catalog
        """
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
        """
        Build the `services` section of the service catalog

        :param dict user_data: dict containing the user data
        :retval: dict containing the service section of the service catalog
        """
        def get_endpoints_for_service(service_id):
            """
            Build the endpoints section of a service's entry in the service
                catalog

            :param integer service_id: the internal service_id of the service
            :retval: dict containing the individual endpoint entries for the
                service catalog
            """
            def log_and_insert(dest, dest_key, source, source_key):
                """
                Log the data and set the key from the source to the
                    destination.

                :param dict dest: dictionary to set the value into
                :param unicode dest_key: key in the `dest` dictionary to hold
                    the data
                :param dict source: dictionary to extract the value from
                :param unicode source_key: key in the `source` dictionary to
                    extract the data
                """
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
                    log_and_insert(
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
        """
        Build the service catalog for the given user and token combination

        :param dict token: dict containing the token data
        :param dict user: dict containing the user data 
        """
        return {
            'serviceCatalog': self.get_auth_service_catalog(user),
            'token': self.get_auth_token_entry(token, user),
            'user': self.get_auth_user_entry(user)
        }

    def password_authenticate(self, password_data):
        """
        Authenticate a user+password combination

        :param dict password_data: dict containing the username and
            password
        :raises: KeystoneUserError if the input data is incorrect
        :raises: KeystoneUserInvalidPasswordError if the password is invalid
            for the user
        :raises: KeystoneUnknownUserError if the user is not found
        :raises: KeystoneDIsabledUserError if the user is valid but disabled
        :retval: dict containing the service catalog

        .. note:: This creates and adds a token for the user to the model data.
        """
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
        """
        Authenticate a user+apikey combination

        :param dict apikey_data: dict containing the username and
            apikey
        :raises: KeystoneUserError if the input data is incorrect
        :raises: KeystoneUserInvalidApikeyError if the apikey is invalid
            for the user
        :raises: KeystoneUnknownUserError if the user is not found
        :raises: KeystoneDIsabledUserError if the user is valid but disabled
        :retval: dict containing the service catalog

        .. note:: This creates and adds a token for the user to the model data.
        """
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
        """
        Authenticate a tenantid + token combination

        :param dict auth_data: dict containing the username and
            token
        :raises: KeystoneUserError if the input data is incorrect
        :raises: KeystoneTenantError if the specified tenant does not match
            the tenant on the token
        :raises: KeystoneUnknownUserError if the user is not found
        :raises: KeystoneDIsabledUserError if the user is valid but disabled
        :retval: dict containing the service catalog
        """
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
        """
        Authenticate a tenant name + token combination

        :param dict auth_data: dict containing the username and
            token
        :raises: KeystoneUserError if the input data is incorrect
        :retval: dict containing the service catalog

        .. note:: see `tenant_id_token_auth` for more details as this
            is a basic wrapper around it for converting from the
            tenant-name to tenant-id.
        """
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
