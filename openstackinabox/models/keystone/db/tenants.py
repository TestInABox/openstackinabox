from openstackinabox.models.keystone import exceptions

from openstackinabox.models.keystone.db.base import KeystoneDbBase


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
    WHERE tenantid = :tenant_id
'''

SQL_GET_ALL_TENANTS = '''
    SELECT tenantid, name, description, enabled
    FROM keystone_tenants
'''

SQL_GET_TENANT_BY_NAME = '''
    SELECT tenantid, name, description, enabled
    FROM keystone_tenants
    WHERE name = :tenant_name
'''

SQL_UPDATE_TENANT_DESCRIPTION = '''
    UPDATE keystone_tenants
    SET description = :description
    WHERE tenantid = :tenant_id
'''

SQL_UPDATE_TENANT_STATUS = '''
    UPDATE keystone_tenants
    SET enabled = :enabled
    WHERE tenantid = :tenant_id
'''


class KeystoneDbTenants(KeystoneDbBase):
    """
    Tenant Model

    :cvar unicode SYSTEM_TENANT_NAME: global system tenant used for the admin
        service user
    :cvar unicode SYSTEM_TENANT_DESCRIPTION: global tenant description
    """

    SYSTEM_TENANT_NAME = 'system'
    SYSTEM_TENANT_DESCRIPTION = 'system administrator'

    def __init__(self, master, db):
        """
        :param ModelDbBase master: master model for cross-referencing
        :param sqlite3 db: Sqlite3 database for data storage
        """
        super(KeystoneDbTenants, self).__init__("KeystoneTenants", master, db)
        self.__admin_tenant_id = None

    def initialize(self):
        """
        Create the built-in tenant
        """
        self.__admin_tenant_id = self.add(
            tenant_name=self.SYSTEM_TENANT_NAME,
            description=self.SYSTEM_TENANT_DESCRIPTION,
            enabled=True
        )

    @property
    def admin_tenant_id(self):
        """
        Access the administrative tenant id
        """
        return self.__admin_tenant_id

    def add(self, tenant_name=None, description=None, enabled=True):
        """
        Add a new tenant

        :param unicode tenant_name: tenant display name
        :param unicode description: account description
        :param boolean enabled: whether or not the account is active
            and available for user
        :raises: KeystoneTenantError
        :retval: int - tenant id
        """
        args = {
            'name': tenant_name,
            'description': description,
            'enabled': self.bool_to_database(enabled)
        }
        dbcursor = self.database.cursor()
        dbcursor.execute(SQL_ADD_TENANT, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneTenantError('Unable to add tenant')

        self.database.commit()

        dbcursor.execute(SQL_GET_MAX_TENANT_ID)
        tenant_data = dbcursor.fetchone()
        if tenant_data is None:
            raise exceptions.KeystoneTenantError(
                'Unable to retrieve tenant_id for newly created tenant'
            )

        tenant_id = tenant_data[0]

        self.log_debug(
            'Added tenant {0} with id {1}'.format(
                tenant_name,
                tenant_id
            )
        )

        return tenant_id

    def get(self):
        """
        Retrieve all tenants

        :retval: list of dict entries, one entry per tenant
        """
        dbcursor = self.database.cursor()
        tenant_list = []
        for row in dbcursor.execute(SQL_GET_ALL_TENANTS):
            tenant_list.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'enabled': self.bool_from_database(row[3])
            })
        return tenant_list

    # TODO(BenjamenMeyer): delete

    def get_by_id(self, tenant_id):
        """
        Get a tenant for a given tenant id

        :param int tenant_id: tenant id of the desired tenant
        :raises: KeystoneTenantError
        :retval: dict containing the tenant information
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id
        }
        dbcursor.execute(SQL_GET_TENANT_BY_ID, args)
        tenant_data = dbcursor.fetchone()
        if tenant_data is None:
            raise exceptions.KeystoneTenantError('Invalid tenant id')

        return {
            'id': tenant_data[0],
            'name': tenant_data[1],
            'description': tenant_data[2],
            'enabled': self.bool_from_database(tenant_data[3])
        }

    def get_by_name(self, tenant_name):
        """
        Get a tenant for a given tenant name

        :param unicode tenant_name: tenant name of the desired tenant
        :raises: KeystoneTenantError
        :retval: dict containing the tenant information


        .. note:: This is not guaranteed to be unique and therefore may
            not return what is expected if multiple tenants have the
            same tenant name, in which case only the first is returned
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_name': tenant_name
        }
        dbcursor.execute(SQL_GET_TENANT_BY_NAME, args)
        tenant_data = dbcursor.fetchone()
        if tenant_data is None:
            raise exceptions.KeystoneTenantError('Invalid tenant name')

        return {
            'id': tenant_data[0],
            'name': tenant_data[1],
            'description': tenant_data[2],
            'enabled': self.bool_from_database(tenant_data[3])
        }

    def update_description(self, tenant_id=None, description=None):
        """
        Update the account description for a given tenant

        :param int tenant_id: tenant id of the desired tenant
        :param unicode description: new account description for the tenant
        :raises: KeystoneTenantError

        .. note:: parameters are keyword parameters but are nonetheless
            required
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'description': description
        }
        dbcursor.execute(SQL_UPDATE_TENANT_DESCRIPTION, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneTenantError('Invalid tenant id')

        self.database.commit()

    def update_status(self, tenant_id=None, enabled=None):
        """
        Update the account active status for a given tenant

        :param int tenant_id: tenant id of the desired tenant
        :param boolean enabled: whether or not the account is enabled
        :raises: KeystoneTenantError

        .. note:: parameters are keyword parameters but are nonetheless
            required
        """
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'enabled': self.bool_to_database(enabled)
        }
        dbcursor.execute(SQL_UPDATE_TENANT_STATUS, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneTenantError('Invalid tenant id')

        self.database.commit()
