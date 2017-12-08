from openstackinabox.models.keystone import exceptions

from openstackinabox.models.keystone.db.base import KeystoneDbBase


SQL_ADD_SERVICE = '''
    INSERT INTO keystone_services
    (name, type)
    VALUES (:name, :type)
'''

SQL_GET_MAX_SERVICE_ID = '''
    SELECT MAX(serviceid)
    FROM keystone_services
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
    """
    Service Model
    """

    def __init__(self, master, db):
        """
        :param ModelDbBase master: master model for cross-referencing
        :param sqlite3 db: Sqlite3 database for data storage
        """
        super(KeystoneDbServices, self).__init__(
            "KeystoneServices", master, db
        )

    def initialize(self):
        """
        Nothing to initialize
        """

    def add(self, service_name, service_type):
        """
        Add a new service

        :param unicode service_name: name of the service
        :param unicode service_type: type of service
        :raises: KeystoneServiceCatalogServiceError
        :retval: int - internal id of the service
        """
        dbcursor = self.database.cursor()
        args = {
            'name': service_name,
            'type': service_type
        }
        dbcursor.execute(SQL_ADD_SERVICE, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneServiceCatalogServiceError(

        service_data = dbcursor.fetchone()
        if service_data is None:
            raise exceptions.KeystoneServiceCatalogServiceError(
                "Unable to add service"
            )

        service_id = service_data[0]

        self.log_debug(
            'Added service {0}'.format(
                service_id
            )
        )

        return service_id

    def get(self, service_id=None):
        """
        Retrieve the service information

        :param int service_id: (optional) internal service id
        :retval: iterable of dict containing the role information

        .. note:: if service_id is not specified then all services
            will be returned
        """
        dbcursor = self.database.cursor()
        args = {}

        query = SQL_GET_SERVICESif service_id is not None:
            args['service_id'] = service_id
            query = SQL_GET_SERVICE_BY_ID

        for service_data in dbcursor.execute(query, args):
            yield {
                'id': service_data[0],
                'name': service_data[1],
                'type': service_data[2]
            }

    def delete(self, service_id):
        """
        Remove the service information

        :param int service_id: internal service id
        :retval: iterable of dict containing the role information
        """
        dbcursor = self.database.cursor()
        args = {
            'service_id': service_id,
        }
        dbcursor.execute(SQL_REMOVE_SERVICE, args)

        if not dbcursor.rowcount:
            raise exceptions.KeystoneServiceCatalogServiceError(
                'Unable to remove service'
            )

        self.database.commit()
