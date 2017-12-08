from openstackinabox.models.keystone import exceptions

from openstackinabox.models.keystone.db.base import KeystoneDbBase


SQL_ADD_ROLE = '''
    INSERT INTO keystone_roles
    (rolename)
    VALUES (:name)
'''

SQL_GET_ROLE_ID = '''
    SELECT roleid, rolename
    FROM keystone_roles
    WHERE rolename = :name
'''

SQL_ADD_USER_ROLE = '''
    INSERT INTO keystone_user_roles
    (tenantid, userid, roleid)
    VALUES (:tenant_id, :user_id, :role_id)
'''

SQL_GET_ROLES_FOR_USER = '''
    SELECT keystone_roles.roleid, keystone_roles.rolename
    FROM keystone_roles, keystone_user_roles
    WHERE keystone_roles.roleid = keystone_user_roles.roleid
      AND keystone_user_roles.tenantid = :tenant_id
      AND keystone_user_roles.userid = :user_id
'''


class KeystoneDbRoles(KeystoneDbBase):
    """
    Service User Role Model

    :cvar unicode IDENTITY_ADMIN_ROLE: global tenant admin group
    :cvar unicode IDENTITY_VIEWER_ROLE: global tenant view-only group
    """

    IDENTITY_ADMIN_ROLE = 'identity:user-admin'
    IDENTITY_VIEWER_ROLE = 'identity:observer'

    def __init__(self, master, db):
        """
        :param ModelDbBase master: master model for cross-referencing
        :param sqlite3 db: Sqlite3 database for data storage
        """
        super(KeystoneDbRoles, self).__init__("KeystoneRoles", master, db)
        self.__admin_role_id = None
        self.__viewer_role_id = None

    @property
    def admin_role_id(self):
        """
        Access the internal role id of the built-in admin group
        """
        return self.__admin_role_id

    @property
    def viewer_role_id(self):
        """
        Access the internal role id for the built-in view-only group
        """
        return self.__viewer_role_id

    def initialize(self):
        """
        Create the built-in groups
        """
        self.__admin_role_id = self.add(self.IDENTITY_ADMIN_ROLE)
        self.__viewer_role_id = self.add(self.IDENTITY_VIEWER_ROLE)

    def add(self, name):
        """
        Add a new role

        :param unicode name: name of the role
        :raises: KeystoneRoleError
        :retval: int - internal id of the role
        """
        dbcursor = self.database.cursor()
        args = {
            'name': name
        }
        dbcursor.execute(SQL_ADD_ROLE, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneRoleError('Unable to add role')

        self.database.commit()

        return self.get(name)['id']

    def get(self, name):
        """
        Retrieve the role information

        :param unicode name: name of the role
        :raises: KeystoneRoleError
        :retval: dict containing the role information
        """
        dbcursor = self.database.cursor()
        args = {
            'name': name
        }
        dbcursor.execute(SQL_GET_ROLE_ID, args)
        role_data = dbcursor.fetchone()
        if role_data is None:
            raise exceptions.KeystoneRoleError('Invalid role name')

        return {
            'id': role_data[0],
            'name': role_data[1]
        }

    def add_user_role_by_id(self, tenant_id=None, user_id=None, role_id=None):
        """
        Map a user to a role using the internal role id

        :param int tenant_id: internal tenant id
        :param int user_id: internal user id
        :param int role_id: internal role id
        :raises: KeystoneRoleError
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'role_id': role_id
        }
        self.log_debug(
            'Associating Tenant ({0}) User ({1}) with Role ({2})'.format(
                tenant_id,
                user_id,
                role_id
            )
        )
        try:
            dbcursor.execute(SQL_ADD_USER_ROLE, args)
        except Exception as ex:
            raise exceptions.KeystoneRoleError(
                'Unable to create role: - {0}'.format(ex)
            )

        if not dbcursor.rowcount:
            raise exceptions.KeystoneRoleError(
                'Unable to assign role to tenant_id/user_id'
            )

    def add_user_role_by_role_name(self, tenant_id=None, user_id=None,
                                   role_name=None):
        """
        Map a user to a role using the role name

        :param int tenant_id: internal tenant id
        :param int user_id: internal user id
        :param unicode role_name: name of the role
        :raises: KeystoneRoleError

        .. note:: If two roles with the same name may have an
            unpredictable result.
        """
        role_data = self.get(name=role_name)
        self.add_user_role_by_id(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_data['id']
        )

    def get_user_roles(self, tenant_id=None, user_id=None):
        """
        Access all roles associated with a given user for a given tenant

        :param int tenant_id: internal tenant id
        :param int user_id: internal user id
        :retval: list of dicts containing all the role information for
            the specified tenant's user-id
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'user_id': user_id
        }
        results = []
        for role_data in dbcursor.execute(SQL_GET_ROLES_FOR_USER, args):
            results.append({
                'id': role_data[0],
                'name': role_data[1]
            })
        return results
