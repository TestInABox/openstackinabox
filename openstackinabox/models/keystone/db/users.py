from openstackinabox.models.keystone import exceptions

from openstackinabox.models.keystone.db.base import KeystoneDbBase


SQL_ADD_USER = '''
    INSERT INTO keystone_users
    (tenantid, username, email, password, apikey, enabled)
    VALUES (:tenant_id, :username, :email, :password, :apikey, :enabled)
'''

SQL_DELETE_USER = '''
    DELETE FROM keystone_users
    WHERE tenantid = :tenant_id
      AND userid = :user_id
'''

SQL_GET_MAX_USER_ID = '''
    SELECT MAX(userid)
    FROM keystone_users
'''

SQL_GET_USER_BY_USERNAME_AND_TENANT = '''
    SELECT tenantid, userid, username, email, password, apikey, enabled
    FROM keystone_users
    WHERE tenantid = :tenant_id AND
          username = :username
'''

SQL_GET_USER_BY_TENANT_ONLY = '''
    SELECT tenantid, userid, username, email, password, apikey, enabled
    FROM keystone_users
    WHERE tenantid = :tenant_id
'''

SQL_GET_USER_BY_USERNAME_ONLY = '''
    SELECT tenantid, userid, username, email, password, apikey, enabled
    FROM keystone_users
    WHERE username = :username
'''

SQL_GET_USER_BY_USERID = '''
    SELECT tenantid, userid, username, email, password, apikey, enabled
    FROM keystone_users
    WHERE tenantid = :tenant_id AND
          userid = :user_id
'''

SQL_UPDATE_USER_BY_USERID = '''
    UPDATE keystone_users
    SET enabled = :enabled,
        email = :email,
        password = :password,
        apikey = :apikey
    WHERE tenantid = :tenant_id AND
          userid = :user_id
'''

SQL_GET_USERS_FOR_TENANT_ID = '''
    SELECT tenantid, userid, username, email, password, apikey, enabled
    FROM keystone_users
    WHERE tenantid = :tenant_id
'''


class KeystoneDbUsers(KeystoneDbBase):
    """
    User Model
    """

    def __init__(self, master, db):
        """
        :param ModelDbBase master: master model for cross-referencing
        :param sqlite3 db: Sqlite3 database for data storage
        """
        super(KeystoneDbUsers, self).__init__("KeystoneUsers", master, db)
        self.__admin_user_id = None

    def initialize(self):
        """
        Create an admin user and add the admin token to that user
        """
        self.__admin_user_id = self.add(
            tenant_id=self.master.tenants.admin_tenant_id,
            username='system',
            email='system@stackinabox',
            password='stackinabox',
            apikey='537461636b496e41426f78'
        )
        self.master.roles.add_user_role_by_id(
            tenant_id=self.master.tenants.admin_tenant_id,
            user_id=self.admin_user_id,
            role_id=self.master.roles.admin_role_id
        )

    @property
    def admin_user_id(self):
        """
        Access the admin service user id
        """
        return self.__admin_user_id

    def add(self, tenant_id=None, username=None, email=None,
            password=None, apikey=None, enabled=True):
        """
        Add a new user to the tenant

        :param int tenant_id: tenant id to create the user for
        :param unicode username: name of the use
        :param unicode email: email address for contacting the user
        :param unicode password: password for the user
        :param unicode apikey: API Key for the user
        :param boolean enabled: whether or not the user is active
        :raises: KeystoneUserError
        :retval: int - internal user id
        """

        args = {
            'tenant_id': tenant_id,
            'username': username,
            'email': email,
            'password': password,
            'apikey': apikey,
            'enabled': self.bool_to_database(enabled)
        }
        dbcursor = self.database.cursor()
        dbcursor.execute(SQL_ADD_USER, args)
        self.database.commit()

        dbcursor.execute(SQL_GET_MAX_USER_ID)
        user_data = dbcursor.fetchone()
        if user_data is None:
            raise exceptions.KeystoneUserError('Unable to add user')

        user_id = user_data[0]

        self.log_debug(
            'Added user {1} with user id {2} to tenant id {0}'.format(
                tenant_id,
                username,
                user_id
            )
        )

        return user_id

    def delete(self, tenant_id=None, user_id=None):
        """
        Remove a user for a given tenant

        :param int tenant_id: tenant id to remove the user from
        :param int user_id: internal user id to remove
        """
        args = {
            'tenant_id': tenant_id,
            'user_id': user_id
        }
        dbcursor = self.database.cursor()
        dbcursor.execute(SQL_DELETE_USER, args)
        dbcursor.fetchone()
        self.database.commit()

    def get_by_id(self, tenant_id=None, user_id=None):
        """
        Get user by id

        :param int tenant_id: tenant id containing the user
        :param int user_id: internal user id of the user
        :raises: KeystoneUnknownUserError
        :retval: dict containing the user information
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'user_id': user_id
        }
        dbcursor.execute(SQL_GET_USER_BY_USERID, args)
        user_data = dbcursor.fetchone()
        if user_data is None:
            raise exceptions.KeystoneUnknownUserError(
                'Invalid tenant_id or user_id'
            )

        return {
            'tenant_id': user_data[0],
            'user_id': user_data[1],
            'username': user_data[2],
            'email': user_data[3],
            'password': user_data[4],
            'apikey': user_data[5],
            'enabled': self.bool_from_database(user_data[6])
        }

    def get_by_name(self, tenant_id=None, username=None):
        """
        Get the user by username

        :param int tenant_id: tenant id containing the user
        :param unicode username: username to lookup
        :raises: KeystoneUnknownUserError
        :retval: dict containing the user information
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'username': username
        }
        dbcursor.execute(SQL_GET_USER_BY_USERNAME_AND_TENANT, args)
        user_data = dbcursor.fetchone()
        if user_data is None:
            raise exceptions.KeystoneUnknownUserError(
                'Invalid tenant_id or username'
            )

        return {
            'tenant_id': user_data[0],
            'user_id': user_data[1],
            'username': user_data[2],
            'email': user_data[3],
            'password': user_data[4],
            'apikey': user_data[5],
            'enabled': self.bool_from_database(user_data[6])
        }

    def get_by_name_or_tenant_id(self, tenant_id=None, username=None):
        """
        Get all users by username or tenant-id

        :param int tenant_id: (optional) tenant id to add the token for
        :param int username: (optional) name of the user to query
        :retval: iterable of the dicts containing the user information

        .. note:: tenant_id or username must be specified; username
            takes precedences. tenant_id is default.
        .. note:: This query may return values across tenants.
        """
        sql_query = None
        args = {}
        if username is not None:
            sql_query = SQL_GET_USER_BY_USERNAME_ONLY
            args['username'] = username
        else:
            sql_query = SQL_GET_USER_BY_TENANT_ONLY
            args['tenant_id'] = tenant_id

        dbcursor = self.database.cursor()
        for user_data in dbcursor.execute(sql_query, args):
            yield {
                'tenant_id': user_data[0],
                'user_id': user_data[1],
                'username': user_data[2],
                'email': user_data[3],
                'password': user_data[4],
                'apikey': user_data[5],
                'enabled': self.bool_from_database(user_data[6])
            }

    def update_by_id(self, tenant_id=None, user_id=None, email=None,
                     password=None, apikey=None, enabled=True):
        """
        Update the user information by user-id

        :param int tenant_id: tenant id to create the user for
        :param int user_id: user id for user
        :param unicode email: email address for contacting the user
        :param unicode password: password for the user
        :param unicode apikey: API Key for the user
        :param boolean enabled: whether or not the user is active
        :raises: KeystoneUnknownUserError

        .. note:: the username is not allowed to be changed
        """

        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'email': email,
            'password': password,
            'apikey': apikey,
            'enabled': enabled
        }
        dbcursor.execute(SQL_UPDATE_USER_BY_USERID, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneUnknownUserError(
                'unable to update user - {0}'.format(args)
            )

        self.database.commit()

    def get_for_tenant_id(self, tenant_id):
        """
        Get all users for a given tenant-id

        :param int tenant_id: tenant id to add the token for
        :retval: list of the dicts containing the user information
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id
        }
        results = []
        for user_data in dbcursor.execute(SQL_GET_USERS_FOR_TENANT_ID, args):
            results.append({
                'tenant_id': user_data[0],
                'user_id': user_data[1],
                'username': user_data[2],
                'email': user_data[3],
                'password': user_data[4],
                'apikey': user_data[5],
                'enabled': self.bool_from_database(user_data[6])
            })
        return results
