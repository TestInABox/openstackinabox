from openstackinabox.models.keystone import exceptions

from openstackinabox.models.keystone.db.base import KeystoneDbBase


SQL_ADD_ENDPOINT = '''
    INSERT INTO keystone_service_endpoints
    (serviceid, region, versionInfo, versionList, versionId)
    VALUES (
        :service_id, :region, :version_info_url, :version_list_url, :version_id
    )
'''

SQL_GET_MAX_ENDPOINT_ID = '''
    SELECT MAX(endpointid)
    FROM keystone_service_endpoints
'''

SQL_GET_ENDPOINT = '''
    SELECT serviceid, endpointid, region, versionInfo, versionList, versionId
    FROM keystone_service_endpoints
    WHERE serviceid = :service_id
'''

SQL_GET_SPECIFIC_ENDPOINT = '''
    SELECT serviceid, endpointid, region, versionInfo, versionList, versionId
    FROM keystone_service_endpoints
    WHERE serviceid = :service_id
      AND endpointid = :endpoint_id
'''

SQL_DELETE_ENDPOINT = '''
    DELETE FROM keystone_service_endpoints
    WHERE serviceid = :service_id
      AND endpointid = :endpoint_id
'''

SQL_ADD_ENDPOINT_URL = '''
    INSERT INTO keystone_service_endpoints_url
    (endpointid, name, url)
    VALUES (:endpoint_id, :name, :url)
'''

SQL_GET_MAX_ENDPOINT_URL_ID = '''
    SELECT MAX(urlid)
    FROM keystone_service_endpoints_url
'''

SQL_GET_ENDPOINT_URL = '''
    SELECT endpointid, urlid, name, url
    FROM keystone_service_endpoints_url
    WHERE endpointid = :endpoint_id
'''

SQL_GET_ENDPOINT_SPECIFIC_URL = '''
    SELECT endpointid, urlid, name, url
    FROM keystone_service_endpoints_url
    WHERE endpointid = :endpoint_id
      AND urlid = :url_id
'''

SQL_DELETE_ENDPOINT_URL = '''
    DELETE FROM keystone_service_endpoints_url
    WHERE endpointid = :endpoint_id
      AND urlid = :url_id
'''


class KeystoneDbServiceEndpoints(KeystoneDbBase):
    """
    Service Endpoint Model
    """

    def __init__(self, master, db):
        """
        :param ModelDbBase master: master model for cross-referencing
        :param sqlite3 db: Sqlite3 database for data storage
        """
        super(KeystoneDbServiceEndpoints, self).__init__(
            "KeystoneServiceEndpoints", master, db
        )

    def initialize(self):
        """
        Nothing to initialize
        """

    def add(self, service_id, region, version_info, version_list, version_id):
        """
        Add an endpoint for an existing service

        :param unicode service_id: internal service id for an existing service
        :param unicode region: datacenter/region for the services
        :param unicode version_info: version information
        :param unicode version_list: version list
        :param int version_id: version identifier
        :raises: KeystoneServiceCatalogEndpointError
        :retval: int - internal endpoint identifier
        """
        dbcursor = self.database.cursor()
        args = {
            'service_id': service_id,
            'region': region,
            'version_info_url': version_info,
            'version_list_url': version_list,
            'version_id': str(version_id)
        }
        dbcursor.execute(SQL_ADD_ENDPOINT, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneServiceCatalogEndpointError(
                'Unable to add service'
            )
        self.database.commit()

        dbcursor.execute(SQL_GET_MAX_ENDPOINT_ID)
        endpoint_data = dbcursor.fetchone()
        if endpoint_data is None:
            raise exceptions.KeystoneServiceCatalogEndpointError(
                "Unable to add endpoint"
            )

        endpoint_id = endpoint_data[0]

        self.log_debug(
            'Added endpoint {0} for service {1}'.format(
                service_id,
                endpoint_id,
            )
        )

        return endpoint_id

    def get(self, service_id, endpoint_id=None):
        """
        Access the endpoint data

        :param int service_id: internal service id for the endpoint data
        :param int endpoint_id: (optional) internal endpoint id

        .. note:: If the endpoint_id is not specified then all of the endpoints
            are returned.

        :retval: iterable of dictionaries that contain the endpoint
            information
        """
        dbcursor = self.database.cursor()
        args = {
            'service_id': service_id
        }

        query = SQL_GET_ENDPOINT
        if endpoint_id is not None:
            args['endpoint_id'] = endpoint_id
            query = SQL_GET_SPECIFIC_ENDPOINT

        for endpoint_data in dbcursor.execute(query, args):
            yield {
                'service_id': endpoint_data[0],
                'endpoint_id': endpoint_data[1],
                'region': endpoint_data[2],
                'version_info': endpoint_data[3],
                'version_list': endpoint_data[4],
                'version_id': endpoint_data[5],
            }

    def delete(self, service_id, endpoint_id):
        """
        Remove the endpoint data

        :param int service_id: internal service id for the endpoint data
        :param int endpoint_id: internal endpoint id
        :raises: KeystoneServiceCatalogEndpointError
        """
        dbcursor = self.database.cursor()
        args = {
            'service_id': service_id,
            'endpoint_id': endpoint_id
        }
        dbcursor.execute(SQL_DELETE_ENDPOINT, args)

        if not dbcursor.rowcount:
            raise exceptions.KeystoneServiceCatalogEndpointError(
                'Unable to remove endpoint for service'
            )

        self.database.commit()

    def add_url(self, endpoint_id, name, url):
        """
        Add a URL for an endpoint

        :param int endpoint_id: internal endpoint id
        :param unicode name: name of the URL
        :param unicode url: URL for the endpoint
        :raises: KeystoneEndpointUrlError
        :retval: int - internal endpoint url id
        """
        dbcursor = self.database.cursor()
        args = {
            'endpoint_id': endpoint_id,
            'name': name,
            'url': url
        }
        dbcursor.execute(SQL_ADD_ENDPOINT_URL, args)
        if not dbcursor.rowcount:
            raise exceptions.KeystoneEndpointUrlError(
                'Unable to add service endpoint url'
            )
        self.database.commit()

        dbcursor.execute(SQL_GET_MAX_ENDPOINT_URL_ID)
        url_data = dbcursor.fetchone()
        if url_data is None:
            raise exceptions.KeystoneEndpointUrlError(
                "Unable to add endpoint url"
            )

        url_id = url_data[0]

        self.log_debug(
            'Added url {1} for endpoint {0}'.format(
                endpoint_id,
                url_id
            )
        )

        return url_id

    def get_url(self, endpoint_id, url_id=None):
        """
        Get the URL(s) for the specified endpoint

        :param int endpoint_id: internal endpoint id
        :param int url_id: (optional) internal endpoint url id

        .. note:: If the url_id is not specified then all of the
            urls are returned.

        :retval: iterable of dictionaries that contain the endpoint
            url information.
        """
        dbcursor = self.database.cursor()
        args = {
            'endpoint_id': endpoint_id
        }

        query = SQL_GET_ENDPOINT_URL
        if url_id is not None:
            args['url_id'] = url_id
            query = SQL_GET_ENDPOINT_SPECIFIC_URL

        for url_data in dbcursor.execute(query, args):
            yield {
                'endpoint_id': url_data[0],
                'url_id': url_data[1],
                'name': url_data[2],
                'url': url_data[3]
            }

    def delete_url(self, endpoint_id, url_id):
        """
        Remove the url for the specified endpoint

        :param int endpoint_id: internal endpoint id
        :param int url_id: (optional) internal endpoint url id
        :raises: KeystoneEndpointUrlError
        """
        dbcursor = self.database.cursor()
        args = {
            'endpoint_id': endpoint_id,
            'url_id': url_id
        }
        dbcursor.execute(SQL_DELETE_ENDPOINT_URL, args)

        if not dbcursor.rowcount:
            raise exceptions.KeystoneEndpointUrlError(
                'Unable to remove endpoint url')

        self.database.commit()
