from openstackinabox.models.keystone.exceptions import *

from openstackinabox.models.keystone.db.base import KeystoneDbBase


SQL_ADD_SERVICE = '''
    INSERT INTO keystone_services
    (name, type)
    VALUES (:name, :type)
'''

SQL_GET_SERVICES = '''
    SELECT serviceid, name, type
    FROM keystone_services
'''

SQL_GET_SERVICE_BY_ID = '''
    SELECT serviceid, name, type
    FROM keystone_services
    WHERE serviceid = :service_id
'''

SQL_REMOVE_SERVICE = '''
    DELETE FROM keystone_services
    WHERE serviceid = :service_id
'''


class KeystoneDbServices(KeystoneDbBase):

    def __init__(self, master, db):
        super(KeystoneDbServices, self).__init__(
            "KeystoneServices", master, db
        )

    def initialize(self):
        pass

    def add(self, service_name, service_type):
        dbcursor = self.database.cursor()
        args = {
            'name': service_name,
            'type': service_type
        }
        dbcursor.execute(SQL_ADD_SERVICE, args)
        if not dbcursor.rowcount:
            raise KeystoneServiceCatalogServiceError('Unable to add service')

    def get(self, service_id=None):
        dbcursor = self.database.cursor()
        args = {}

        query = SQL_GET_SERVICES
        if service_id is not None:
            args['service_id'] = service_id
            query = SQL_GET_SERVICE_BY_ID

        for service_data in dbcursor.execute(query, args):
            yield {
                'id': service_data[0],
                'name': service_data[1],
                'type': service_data[2]
            }

    def delete(self, service_id):
        dbcursor = self.database.cursor()
        args = {
            'service_id': service_id,
        }
        dbcursor.execute(SQL_REMOVE_SERVICE, args)

        if not dbcursor.rowcount:
            raise KeystoneServiceCatalogServiceError(
                'Unable to remove service'
            )

        self.database.commit()
