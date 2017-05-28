"""
OpenStack Keystone Model
"""
import datetime
import random
import re
import sqlite3
import uuid


from openstackinabox.models.base_model import *


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
    '''
]

SQL_ADD_TENANT = '''
    INSERT INTO keystone_tenants
    (name, description, enabled)
    VALUES(:name, :description, :enabled)
'''

SQL_GET_MAX_TENANT_ID = '''
    SELECT MAX(tenantid)
    FROM keystone_tenants
'''

SQL_GET_TENANT_BY_ID = '''
    SELECT tenantid, name, description, enabled
    FROM keystone_tenants
    WHERE tenantid = :tenantid
'''

SQL_GET_ALL_TENANTS = '''
    SELECT tenantid, name, description, enabled
    FROM keystone_tenants
'''

SQL_GET_TENANT_BY_NAME = '''
    SELECT tenantid, name, description, enabled
    FROM keystone_tenants
    WHERE name = :tenantname
'''

SQL_UPDATE_TENANT_DESCRIPTION = '''
    UPDATE keystone_tenants
    SET description = :description
    WHERE tenantid = :tenantid
'''

SQL_UPDATE_TENANT_STATUS = '''
    UPDATE keystone_tenants
    SET enabled = :enabled
    WHERE tenantid = :tenantid
'''

SQL_ADD_USER = '''
    INSERT INTO keystone_users
    (tenantid, username, email, password, apikey, enabled)
    VALUES (:tenantid, :username, :email, :password, :apikey, :enabled)
'''

SQL_DELETE_USER = '''
    DELETE FROM keystone_users
    WHERE tenantid = :tenantid
      AND userid = :userid
'''

SQL_GET_MAX_USER_ID = '''
    SELECT MAX(userid)
    FROM keystone_users
'''

SQL_GET_USER_BY_USERNAME = '''
    SELECT tenantid, userid, username, email, password, apikey, enabled
    FROM keystone_users
    WHERE tenantid = :tenantid AND
          username = :username
'''

SQL_GET_USER_BY_USERID = '''
    SELECT tenantid, userid, username, email, password, apikey, enabled
    FROM keystone_users
    WHERE tenantid = :tenantid AND
          userid = :userid
'''

SQL_UPDATE_USER_BY_USERID = '''
    UPDATE keystone_users
    SET enabled = :enabled,
        email = :email,
        password = :password,
        apikey = :apikey
    WHERE tenantid = :tenantid AND
          userid = :userid
'''

SQL_GET_USERS_FOR_TENANT_ID = '''
    SELECT tenantid, userid, username, email, password, apikey, enabled
    FROM keystone_users
    WHERE tenantid = :tenantid
'''

SQL_INSERT_TOKEN = '''
    INSERT INTO keystone_tokens
    (tenantid, userid, token, ttl, revoked)
    VALUES(:tenantid, :userid, :token, DATETIME('NOW', '+12 HOURS'), 0)
'''

SQL_INSERT_TOKEN_AND_EXPIRATION = '''
    INSERT INTO keystone_tokens
    (tenantid, userid, token, ttl, revoked)
    VALUES(:tenantid, :userid, :token, :ttl, 0)
'''

SQL_GET_TOKEN_BY_TENANT_ID = '''
    SELECT tenantid, userid, token, ttl, revoked
    FROM keystone_tokens
    WHERE tenantid = :tenantid
'''

SQL_GET_TOKEN_BY_USER_ID = '''
    SELECT tenantid, userid, token, ttl, revoked
    FROM keystone_tokens
    WHERE userid = :userid
'''

SQL_GET_TOKEN_BY_USER_NAME = '''
    SELECT keystone_tokens.tenantid, keystone_tokens.userid,
           keystone_tokens.token, keystone_tokens.ttl, keystone_tokens.revoked
    FROM keystone_tokens, keystone_users
    WHERE keystone_tokens.tenantid = keystone_users.tenantid
      AND keystone_tokens.userid = keystone_users.userid
      AND keystone_users.username = :username
'''

SQL_REVOKE_TOKEN = '''
    UPDATE keystone_tokens
    SET revoked = 1
    WHERE tenantid = :tenantid
      AND userid = :userid
'''

SQL_RESET_REVOKED_TOKEN = '''
    UPDATE keystone_tokens
    SET revoked = 0
    WHERE tenantid = :tenantid
      AND userid = :userid
'''

SQL_VALIDATE_TOKEN = '''
    SELECT tenantid, userid, token, ttl, revoked
    FROM keystone_tokens
    WHERE token = :token
'''

SQL_ADD_ROLE = '''
    INSERT INTO keystone_roles
    (rolename)
    VALUES (:rolename)
'''

SQL_GET_ROLE_ID = '''
    SELECT roleid, rolename
    FROM keystone_roles
    WHERE rolename = :rolename
'''

SQL_ADD_USER_ROLE = '''
    INSERT INTO keystone_user_roles
    (tenantid, userid, roleid)
    VALUES (:tenantid, :userid, :roleid)
'''

SQL_GET_ROLES_FOR_USER = '''
    SELECT keystone_roles.roleid, keystone_roles.rolename
    FROM keystone_roles, keystone_user_roles
    WHERE keystone_roles.roleid = keystone_user_roles.roleid
      AND keystone_user_roles.tenantid = :tenantid
      AND keystone_user_roles.userid = :userid
'''


class KeystoneError(BaseModelExceptions):
    pass


class KeystoneTenantError(KeystoneError):
    pass


class KeystoneUserError(KeystoneError):
    pass


class KeystoneUnknownUserError(KeystoneUserError):
    pass


class KeystoneTokenError(KeystoneError):
    pass


class KeystoneInvalidTokenError(KeystoneTokenError):
    pass


class KeystoneRevokedTokenError(KeystoneInvalidTokenError):
    pass


class KeystoneExpiredTokenError(KeystoneInvalidTokenError):
    pass


class KeystoneRoleError(KeystoneError):
    pass


class KeystoneModel(BaseModel):

    IDENTITY_ADMIN_ROLE = 'identity:user-admin'
    IDENTITY_VIEWER_ROLE = 'identity:observer'

    def __init__(self):
        super(KeystoneModel, self).__init__('KeystoneModel')
        self.__admin_token = 'adminstrate_with_this_{0}'.format(uuid.uuid4())
        self.database = sqlite3.connect(':memory:')
        self.init_database()

    @staticmethod
    def make_token():
        return uuid.uuid4()

    @staticmethod
    def bool_from_database(value):
        if value:
            return True
        return False

    @staticmethod
    def bool_to_database(value):
        if value:
            return 1
        return 0

    def add_admin_tenant_details(self):
        self.__admin_tenant_args = {
            'name': 'system',
            'description': 'system administrator',
        }

    def add_admin_user_details(self):
        self.__admin_user_args = {
            'tenantid': self.__admin_tenant_id,
            'username': 'system',
            'email': 'system@stackinabox',
            'password': 'stackinabox',
            'apikey': '537461636b496e41426f78',
        }

    @property
    def get_admin_tenant_details(self):
        return self.get_tenant_by_id(self.__admin_tenant_id)

    @property
    def get_admin_user_details(self):
        return self.get_user_by_id(self.__admin_tenant_id,
            self.__admin_user_id)

    def init_database(self):
        self.log_info('Initializing database')
        dbcursor = self.database.cursor()
        for table_sql in schema:
            dbcursor.execute(table_sql)

        # Create an admin user and add the admin token to that user
        self.__admin_tenant_id = self.add_tenant('system',
                                                 'system administrator')

        self.__admin_user_id = self.add_user(self.__admin_tenant_id,
                                             'system',
                                             'system@stackinabox',
                                             'stackinabox',
                                             '537461636b496e41426f78')

        roles = [
            KeystoneModel.IDENTITY_ADMIN_ROLE,
            KeystoneModel.IDENTITY_VIEWER_ROLE,
        ]
        for role in roles:
            role_data = self.add_role(role)
            if role == KeystoneModel.IDENTITY_ADMIN_ROLE:
                self.__admin_role_id = role_data['roleid']
                self.add_user_role_by_roleid(self.__admin_tenant_id,
                                             self.__admin_user_id,
                                             self.__admin_role_id)

        self.add_token(self.__admin_tenant_id,
                       self.__admin_user_id,
                       token=self.__admin_token)

        self.database.commit()
        self.log_info('Database initialized')

    def validate_username(self, username):
        self.log_debug('Validating username {0}'.format(username))
        regex = re.compile('^[a-zA-Z]+[\w\.@-]*$')
        if regex.match(username) is None:
            self.log_debug('Username {0} is INVALID'.format(username))
            return False

        self.log_debug('Username {0} is valid'.format(username))
        return True

    def validate_password(self, password):
        self.log_debug('Validating password {0}'.format(password))
        regexes = [
            re.compile('^[a-zA-Z]+[\w\.@-]*$'),
            re.compile('[\w\W]*[A-Z]+'),
            re.compile('[\w\W]*[a-z]+'),
            re.compile('[\w\W]*[0-9]+')
        ]

        for regex in regexes:
            if regex.match(password) is None:
                self.log_debug('password {1} validation failed regex {0}'
                               .format(regex.pattern, password))
                return False

        self.log_debug('password {0} is valid'.format(password))
        return True

    def get_admin_token(self):
        return self.__admin_token

    def add_tenant(self, tenantname=None, description=None, enabled=True):
        args = {
            'name': tenantname,
            'description': description,
            'enabled': KeystoneModel.bool_to_database(enabled)
        }
        dbcursor = self.database.cursor()
        dbcursor.execute(SQL_ADD_TENANT, args)
        if not dbcursor.rowcount:
            raise KeystoneTenantError('Unable to add tenant')

        self.database.commit()

        dbcursor.execute(SQL_GET_MAX_TENANT_ID)
        tenant_data = dbcursor.fetchone()
        if tenant_data is None:
            raise KeystoneTenantError(
                'Unable to retrieve tenantid for newly created tenant')

        tenantid = tenant_data[0]

        self.log_debug('Added tenant {0} with id {1}'
                       .format(tenantname, tenantid))

        return tenantid

    def get_tenants(self):
        dbcursor = self.database.cursor()
        tenant_list = []
        for row in dbcursor.execute(SQL_GET_ALL_TENANTS):
            tenant_list.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'enabled': KeystoneModel.bool_from_database(row[3])
            })
        return tenant_list

    def get_tenant_by_id(self, tenantid=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid
        }
        dbcursor.execute(SQL_GET_TENANT_BY_ID, args)
        tenant_data = dbcursor.fetchone()
        if tenant_data is None:
            raise KeystoneTenantError('Invalid tenant id')

        return {
            'id': tenant_data[0],
            'name': tenant_data[1],
            'description': tenant_data[2],
            'enabled': KeystoneModel.bool_from_database(tenant_data[3])
        }

    def get_tenant_by_name(self, tenantname=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantname': tenantname
        }
        dbcursor.execute(SQL_GET_TENANT_BY_NAME, args)
        tenant_data = dbcursor.fetchone()
        if tenant_data is None:
            raise KeystoneTenantError('Invalid tenant name')

        return {
            'id': tenant_data[0],
            'name': tenant_data[1],
            'description': tenant_data[2],
            'enabled': KeystoneModel.bool_from_database(tenant_data[3])
        }

    def update_tenant_description(self, tenantid=None, description=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'description': description
        }
        dbcursor.execute(SQL_UPDATE_TENANT_DESCRIPTION, args)
        if not dbcursor.rowcount:
            raise KeystoneTenantError('Invalid tenant id')

        self.database.commit()

    def update_tenant_status(self, tenantid=None, enabled=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'enabled': KeystoneModel.bool_to_database(enabled)
        }
        dbcursor.execute(SQL_UPDATE_TENANT_STATUS, args)
        if not dbcursor.rowcount:
            raise KeystoneTenantError('Invalid tenant id')

        self.database.commit()

    def add_user(self, tenantid=None, username=None, email=None,
                 password=None, apikey=None, enabled=True):
        args = {
            'tenantid': tenantid,
            'username': username,
            'email': email,
            'password': password,
            'apikey': apikey,
            'enabled': KeystoneModel.bool_to_database(enabled)
        }
        dbcursor = self.database.cursor()
        dbcursor.execute(SQL_ADD_USER, args)
        self.database.commit()

        dbcursor.execute(SQL_GET_MAX_USER_ID)
        user_data = dbcursor.fetchone()
        if user_data is None:
            raise KeystoneUserError('Unable to add user')

        userid = user_data[0]

        self.log_debug('Added user {1} with user id {2} to tenant id {0}'
                       .format(tenantid, username, userid))

        return userid

    def delete_user(self, tenantid=None, userid=None):
        args = {
            'tenantid': tenantid,
            'userid': userid
        }
        dbcursor = self.database.cursor()
        dbcursor.execute(SQL_DELETE_USER, args)
        user_data = dbcursor.fetchone()
        self.database.commit()

    def get_user_by_id(self, tenantid=None, userid=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'userid': userid
        }
        dbcursor.execute(SQL_GET_USER_BY_USERID, args)
        user_data = dbcursor.fetchone()
        if user_data is None:
            raise KeystoneUnknownUserError('Invalid tenantid or userid')

        return {
            'tenantid': user_data[0],
            'userid': user_data[1],
            'username': user_data[2],
            'email': user_data[3],
            'password': user_data[4],
            'apikey': user_data[5],
            'enabled': KeystoneModel.bool_from_database(user_data[6])
        }

    def get_user_by_name(self, tenantid=None, username=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'username': username
        }
        dbcursor.execute(SQL_GET_USER_BY_USERNAME, args)
        user_data = dbcursor.fetchone()
        if user_data is None:
            raise KeystoneUnknownUserError('Invalid tenantid or username')

        return {
            'tenantid': user_data[0],
            'userid': user_data[1],
            'username': user_data[2],
            'email': user_data[3],
            'password': user_data[4],
            'apikey': user_data[5],
            'enabled': KeystoneModel.bool_from_database(user_data[6])
        }

    def update_user_by_user_id(self, tenantid=None, userid=None, email=None,
                               password=None, apikey=None, enabled=True):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'userid': userid,
            'email': email,
            'password': password,
            'apikey': apikey,
            'enabled': enabled
        }
        dbcursor.execute(SQL_UPDATE_USER_BY_USERID, args)
        if not dbcursor.rowcount:
            raise KeystoneUnknownUserError('unable to update user - {0}'
                                           .format(args))

        self.database.commit()

    def get_users_for_tenant_id(self, tenantid=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid
        }
        results = []
        for user_data in dbcursor.execute(SQL_GET_USERS_FOR_TENANT_ID, args):
            results.append({
                'tenantid': user_data[0],
                'userid': user_data[1],
                'username': user_data[2],
                'email': user_data[3],
                'password': user_data[4],
                'apikey': user_data[5],
                'enabled': KeystoneModel.bool_from_database(user_data[6])
            })
        return results

    def add_token(self, tenantid=None, userid=None,
                  expire_time=None, token=None):
        if token is None:
            token = uuid.uuid4()

        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'userid': userid,
            'token': str(token)
        }
        if expire_time is not None:
            if not isinstance(expire_time, datetime.datetime):
                raise TypeError(
                    'expire_time must be a datetime.datetime object')

            '''2015-02-03 02:31:17'''
            utc_expire_time = expire_time.utctimetuple()
            args['ttl'] = '{0}-{1}-{2} {3}:{4}:5'.format(
                utc_expire_time[0],
                utc_expire_time[1],
                utc_expire_time[2],
                utc_expire_time[3],
                utc_expire_time[4],
                utc_expire_time[5])
            dbcursor.execute(SQL_INSERT_TOKEN_AND_EXPIRATION, args)
        else:
            dbcursor.execute(SQL_INSERT_TOKEN, args)

        if not dbcursor.rowcount:
            raise KeystoneTokenError('Unable to add token')

        self.database.commit()
        return token

    def revoke_token(self, tenantid=None, userid=None, reset=False):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'userid': userid
        }
        if reset:
            dbcursor.execute(SQL_RESET_REVOKED_TOKEN, args)
        else:
            dbcursor.execute(SQL_REVOKE_TOKEN, args)

        if not dbcursor.rowcount:
            raise KeystoneTokenError(
                'Unknown tenantid or  userid; or no associated token')

        self.database.commit()

    def get_token_by_userid(self, userid=None):
        dbcursor = self.database.cursor()
        args = {
            'userid': userid
        }
        dbcursor.execute(SQL_GET_TOKEN_BY_USER_ID, args)
        token_data = dbcursor.fetchone()
        if token_data is None:
            raise KeystoneUnknownUserError('Unknown userid - {0}'
                                           .format(userid))

        return {
            'tenantid': token_data[0],
            'userid': token_data[1],
            'token': token_data[2],
            'expires': token_data[3],
            'revoked': KeystoneModel.bool_from_database(token_data[4])
        }

    def get_token_by_tenantid(self, tenantid=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid
        }
        results = []
        for token_data in dbcursor.execute(SQL_GET_TOKEN_BY_TENANT_ID, args):
            results.append({
                'tenantid': token_data[0],
                'userid': token_data[1],
                'token': token_data[2],
                'expires': token_data[3],
                'revoked': KeystoneModel.bool_from_database(token_data[4])
            })
        return results

    def get_token_by_username(self, username=None):
        dbcursor = self.database.cursor()
        args = {
            'username': username
        }
        dbcursor.execute(SQL_GET_TOKEN_BY_USER_NAME, args)
        token_data = dbcursor.fetchone()
        if token_data is None:
            raise KeystoneUnknownUserError('Unknown username')

        return {
            'tenantid': token_data[0],
            'userid': token_data[1],
            'token': token_data[2],
            'expires': token_data[3],
            'revoked': KeystoneModel.bool_from_database(token_data[4])
        }

    def add_role(self, rolename=None):
        dbcursor = self.database.cursor()
        args = {
            'rolename': rolename
        }
        dbcursor.execute(SQL_ADD_ROLE, args)
        if not dbcursor.rowcount:
            raise KeystoneRoleError('Unable to add role')

        self.database.commit()

        return self.get_role_id(rolename)

    def get_role_id(self, rolename=None):
        dbcursor = self.database.cursor()
        args = {
            'rolename': rolename
        }
        dbcursor.execute(SQL_GET_ROLE_ID, args)
        role_data = dbcursor.fetchone()
        if role_data is None:
            raise KeystoneRoleError('Invalid rolename')

        return {
            'roleid': role_data[0],
            'rolename': role_data[1]
        }

    def add_user_role_by_roleid(self, tenantid=None, userid=None, roleid=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'userid': userid,
            'roleid': roleid
        }
        dbcursor.execute(SQL_ADD_USER_ROLE, args)
        if not dbcursor.rowcount:
            raise KeystoneRoleError('Unable to assign role to tenantid/userid')

    def add_user_role_by_rolename(self, tenantid=None, userid=None,
                                  rolename=None):
        role_data = self.get_role_id(rolename)
        self.add_user_role_by_roleid(tenantid, userid, role_data['roleid'])

    def get_roles_for_user(self, tenantid=None, userid=None):
        dbcursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'userid': userid
        }
        results = []
        for role_data in dbcursor.execute(SQL_GET_ROLES_FOR_USER, args):
            results.append({
                'roleid': role_data[0],
                'rolename': role_data[1]
            })
        return results

    def validate_token(self, token):
        dbcursor = self.database.cursor()
        args = {
            'token': token
        }
        dbcursor.execute(SQL_VALIDATE_TOKEN, args)
        token_data = dbcursor.fetchone()
        if token_data is None:
            raise KeystoneInvalidTokenError('Invalid token')

        result = {
            'tenantid': token_data[0],
            'userid': token_data[1],
            'token': token_data[2],
            'expires': token_data[3],
            'revoked': KeystoneModel.bool_from_database(token_data[4])
        }
        if result['revoked']:
            raise KeystoneRevokedTokenError('Token was revoked')

        # 2015-02-03 02:30:58
        expire_time = datetime.datetime.strptime(result['expires'],
                                                 '%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.utcnow()
        if expire_time < now:
            raise KeystoneExpiredTokenError('Token expired ({0} >= {1})'
                                            .format(expire_time, now))

        return result

    def validate_token_admin(self, token):
        try:
            self.log_debug('Checking token {0} for registration...'
                           .format(token))
            user_data = self.validate_token(token)

            self.log_debug('Token is valid.')
            self.log_debug('Accessing user credentials for {0}/{1}...'
                           .format(user_data['tenantid'],
                                   user_data['userid']))
            user_roles = self.get_roles_for_user(user_data['tenantid'],
                                                 user_data['userid'])
            self.log_debug('User has {0} roles...'
                           .format(len(user_roles)))
            for role_data in user_roles:
                roleid = role_data['roleid']
                rolename = role_data['rolename']
                self.log_debug('Checking against role {0} - {1}'
                               .format(roleid, rolename))
                if rolename == KeystoneModel.IDENTITY_ADMIN_ROLE:
                    self.log_debug('User has {0} role'
                                   .format(KeystoneModel.IDENTITY_ADMIN_ROLE))
                    return user_data

        except Exception as ex:
            self.log_exception('Error: {0}'.format(ex))

        raise KeystoneInvalidTokenError('Invalid Token')

    def validate_token_service_admin(self, token):
        try:
            self.log_debug('Checking token {0} for validity...'
                           .format(token))
            user_data = self.validate_token_admin(token)

            self.log_debug('Checking if token {0} is the sole service admin '
                           'token...'
                           .format(token))

            if token == self.get_admin_token():
                self.log_debug('Token {0} validated.'.format(token))
                return user_data

        except Exception as ex:
            self.log_exception('Error: {0}'.format(ex))

        raise KeystoneInvalidTokenError('Not the service admin token')
