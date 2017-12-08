import re
import uuid

import six

from openstackinabox.models.base_db import ModelDbBase


class KeystoneDbBase(ModelDbBase):
    """
    Base Keystone Model providing some common functionality
    """

    def __init__(self, name, master, db):
        """
        :param unicode name: name of the model
        :param ModelDbBase master: master model for cross-referencing
        :param sqlite3 db: Sqlite3 database for data storage
        """
        super(KeystoneDbBase, self).__init__(name, master, db)

    @staticmethod
    def make_token():
        """
        Generate an auth-token value

        :retval: unicode containing the auth token
        """
        return str(uuid.uuid4())

    def validate_username(self, username):
        """
        Validate the username meets the Keystone requirements for a username
            per the documentation

        :param unicode name: username to validate
        :retval: boolean - True if valid, otherwise False
        """
        self.log_debug('Validating username {0}'.format(username))
        regex = re.compile('^[a-zA-Z]+[\w\.@-]*$')
        if regex.match(username) is None:
            self.log_debug('Username {0} is INVALID'.format(username))
            return False

        self.log_debug('Username {0} is valid'.format(username))
        return True

    def validate_tenant_name(self, tenant_name):
        """
        Validate the tenant name meets the Keystone requirements for a tenant
            name per the documentation

        :param unicode name: tenant name to validate
        :retval: boolean - True if valid, otherwise False
        """
        self.log_debug('Validating tenant name {0}'.format(tenant_name))
        regex = re.compile('^[a-zA-Z]+[\w\.@-]*$')
        if regex.match(tenant_name) is None:
            self.log_debug('tenant name {0} is INVALID'.format(tenant_name))
            return False

        self.log_debug('Username {0} is valid'.format(tenant_name))
        return True

    def validate_tenant_id(self, tenant_id):
        """
        Validate the tenant id meets the Keystone requirements for a tenant
            id per the implementation

        :param int name: tenant id to validate
        :retval: boolean - True if valid, otherwise False
        """
        self.log_debug('Validating tenant id {0}'.format(tenant_id))
        if not isinstance(tenant_id, int):
            self.log_debug('tenant id {0} is INVALID'.format(tenant_id))
            return False

        self.log_debug('Tenant ID {0} is valid'.format(tenant_id))
        return True

    def validate_password(self, password):
        """
        Validate the password meets the Keystone requirements for a password
            per the implementation

        :param unicode password: password to validate
        :retval: boolean - True if valid, otherwise False
        """
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

    def validate_apikey(self, apikey):
        """
        Validate the apikey meets the Keystone requirements for a API Key
            per the implementation

        :param unicode apikey: API Key to validate
        :retval: boolean - True if valid, otherwise False
        """
        return isinstance(apikey, six.string_types)

    def validate_token(self, token):
        """
        Validate the token meets the Keystone requirements for a token
            per the implementation

        :param unicode token: token to validate
        :retval: boolean - True if valid, otherwise False
        """
        return isinstance(token, six.string_types)
