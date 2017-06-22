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

    SYSTEM_TENANT_NAME = 'system'
    SYSTEM_TENANT_DESCRIPTION = 'system administrator'

    def __init__(self, master, db):
        super(KeystoneDbTenants, self).__init__("KeystoneTenants", master, db)
        self.__admin_tenant_id = None

    def initialize(self):
        self.__admin_tenant_id = self.add(
            tenant_name=self.SYSTEM_TENANT_NAME,
            description=self.SYSTEM_TENANT_DESCRIPTION,
            enabled=True
        )

    @property
    def admin_tenant_id(self):
        return self.__admin_tenant_id

    def add(self, tenant_name=None, description=None, enabled=True):
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
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'enabled': self.bool_to_database(enabled)
        }
        dbcursor.execute(SQL_UPDATE_TENANT_STATUS, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneTenantError('Invalid tenant id')

        self.database.commit()
