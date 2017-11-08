"""
OpenStack Swift Model
"""
import sqlite3

from openstackinabox.models import base_model
from openstackinabox.models.swift import exceptions


schema = [
    '''
    CREATE TABLE swift_tenants
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenantid TEXT NOT NULL,
        path TEXT NOT NULL
    )
    ''',
    '''
    CREATE TABLE swift_containers
    (
        tenantid INTEGER NOT NULL REFERENCES swift_tenants(id),
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_name TEXT NOT NULL,
        path TEXT NOT NULL
    )
    ''',
    '''
    CREATE TABLE swift_objects
    (
        tenantid INTEGER NOT NULL REFERENCES swift_tenants(id),
        containerid INTEGER NOT NULL REFERENCES swift_containers(id),
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        object_name TEXT NOT NULL,
        path TEXT NOT NULL
    )
    '''
]

SQL_INSERT_TENANT = '''
    INSERT INTO swift_tenants
    (tenantid, path)
    VALUES(:tenantid, :path)
'''
SQL_GET_TENANT = '''
    SELECT id, tenantid, path
    FROM swift_tenants
    WHERE id = :id
'''
SQL_HAS_TENANT = '''
    SELECT id
    FROM swift_tenants
    WHERE tenantid = :tenantid
'''

SQL_INSERT_CONTAINER = '''
    INSERT INTO swift_containers
    (tenantid, container_name, path)
    VALUES (:tenantid, :container_name, :path)
'''
SQL_GET_CONTAINER = '''
    SELECT tenantid, id, container_name, path
    FROM swift_containers
    WHERE tenantid = :tenantid
      AND id = :containerid
'''
SQL_HAS_CONTAINER = '''
    SELECT id
    FROM swift_containers
    WHERE tenantid = :tenantid
      AND container_name = :container_name
'''

SQL_INSERT_OBJECT = '''
    INSERT INTO swift_objects
    (tenantid, containerid, object_name, path)
    VALUES(:tenantid, :containerid, :object_name, :path)
'''
SQL_GET_OBJECT = '''
    SELECT tenantid, containerid, id, object_name, path
    FROM swift_objects
    WHERE tenantid = :tenantid
      AND containerid = :containerid
      AND id = :objectid
'''
SQL_HAS_OBJECT = '''
    SELECT id
    FROM swift_objects
    WHERE tenantid = :tenantid
      AND containerid = :containerid
      AND object_name = :object_name
'''
SQL_REMOVE_DELETE = '''
    DELETE
    FROM swift_objects
    WHERE tenantid = :tenantid
      AND containerid = :containerid
      AND id = :objectid
'''


class SwiftServiceModel(base_model.BaseModel):

    @staticmethod
    def initialize_db_schema(db_instance):
        cursor = db_instance.cursor()
        for table_sql in schema:
            cursor.execute(table_sql)
        db_instance.commit()

    def __init__(self, initialize=True):
        super(SwiftServiceModel, self).__init__('SwiftModel')
        self.__db = sqlite3.connect(':memory:')
        if initialize:
            self.initialize_db_schema(self.database)

    @property
    def database(self):
        return self.__db

    def has_tenant(self, tenantid):
        cursor = self.database.cursor()
        args = {
            'tenantid': tenantid
        }
        cursor.execute(SQL_HAS_TENANT, args)
        result = cursor.fetchone()
        if result is None:
            raise exceptions.SwiftUnknownTenantError(
                'Unknown tenant {0}'.format(tenantid)
            )

        return result[0]

    def add_tenant(self, tenantid, path):
        cursor = self.database.cursor()
        args = {
            'tenantid': tenantid,
            'path': path
        }
        cursor.execute(SQL_INSERT_TENANT, args)
        self.database.commit()

        return self.has_tenant(tenantid)

    def get_tenant(self, internal_tenant_id):
        cursor = self.database.cursor()
        args = {
            'id': internal_tenant_id
        }
        cursor.execute(SQL_GET_TENANT, args)
        result = cursor.fetchone()
        if result is None:
            raise exceptions.SwiftUnknownTenantError(
                'Unknown tenant with internal id {0}'.format(
                    internal_tenant_id
                )
            )

        return {
            'id': result[0],
            'tenantid': result[1],
            'path': result[2]
        }

    def has_container(self, internal_tenant_id, container_name):
        cursor = self.database.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'container_name': container_name
        }
        cursor.execute(SQL_HAS_CONTAINER, args)
        result = cursor.fetchone()
        if result is None:
            raise exceptions.SwiftUnknownContainerError(
                'Unknown container {1} under internal tenant id {0}'
                .format(internal_tenant_id, container_name))

        return result[0]

    def add_container(self, internal_tenant_id, container_name, path):
        cursor = self.database.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'container_name': container_name,
            'path': path
        }
        cursor.execute(SQL_INSERT_CONTAINER, args)
        self.database.commit()

        return self.has_container(internal_tenant_id, container_name)

    def get_container(self, internal_tenant_id, internal_container_id):
        cursor = self.database.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id
        }
        cursor.execute(SQL_GET_CONTAINER, args)
        result = cursor.fetchone()
        if result is None:
            raise exceptions.SwiftUnknownContainerError(
                'Unknown container {1} under internal tenant id {0}'
                .format(
                    internal_tenant_id, internal_container_id
                )
            )

        return {
            'tenantid': result[0],
            'containerid': result[1],
            'container_name': result[2],
            'path': result[3]
        }

    def has_object(self, internal_tenant_id, internal_container_id,
                   object_name):
        cursor = self.database.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id,
            'object_name': object_name
        }
        cursor.execute(SQL_HAS_OBJECT, args)
        result = cursor.fetchone()
        if result is None:
            raise exceptions.SwiftUnknownObjectError(
                'Unknown object {2} with internal container id {1} '
                'under internal tenant id {0}'
                .format(internal_tenant_id,
                        internal_container_id,
                        object_name))

        return result[0]

    def add_object(self, internal_tenant_id, internal_container_id,
                   object_name, path):
        cursor = self.database.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id,
            'object_name': object_name,
            'path': path
        }
        cursor.execute(SQL_INSERT_OBJECT, args)
        self.database.commit()

        return self.has_object(internal_tenant_id,
                               internal_container_id,
                               object_name)

    def get_object(
        self, internal_tenant_id, internal_container_id, internal_object_id
    ):
        cursor = self.database.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id,
            'objectid': internal_object_id,
        }
        cursor.execute(SQL_GET_OBJECT, args)
        result = cursor.fetchone()
        if result is None:
            raise exceptions.SwiftUnknownObjectError(
                'Unknown object {2} with internal container id {1} '
                'under internal tenant id {0}'
                .format(
                    internal_tenant_id,
                    internal_container_id,
                    internal_object_id
                )
            )

        return {
            'tenantid': result[0],
            'containerid': result[1],
            'objectid': result[2],
            'object_name': result[3],
            'path': result[4]
        }

    def remove_object(self, internal_tenant_id, internal_container_id,
                      internal_object_id):
        cursor = self.database.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id,
            'objectid': internal_object_id,
        }
        cursor.execute(SQL_REMOVE_DELETE, args)
        self.database.commit()
