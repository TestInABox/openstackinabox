import sqlite3
import unittest

from openstackinabox.models.keystone.model import KeystoneModel


class DbFailure(object):

    def __init__(self, rowcount=0, fetchone=None):
        self._row_count = rowcount
        self._fetch_one = fetchone

    def cursor(self):
        return self

    def execute(self, *args, **kwargs):
        pass

    @property
    def rowcount(self):
        return self._row_count

    def fetchone(self):
        return self._fetch_one

    def commit(self):
        pass


class TestBase(unittest.TestCase):

    @staticmethod
    def get_testing_database(initialize_schema=True):
        db_instance = sqlite3.connect(":memory:")
        if initialize_schema:
            from openstackinabox.models.keystone.model import KeystoneModel
            KeystoneModel.initialize_db_schema(db_instance)

        return db_instance

    def setUp(self, initialize=True):
        super(TestBase, self).setUp()
        self.master_model = KeystoneModel(initialize=initialize)

    def tearDown(self):
        super(TestBase, self).tearDown()

    @property
    def services(self):
        return self.master_model.services

    @property
    def endpoints(self):
        return self.master_model.endpoints

    @property
    def tenants(self):
        return self.master_model.tenants

    @property
    def tokens(self):
        return self.master_model.tokens

    @property
    def users(self):
        return self.master_model.users

    @property
    def roles(self):
        return self.master_model.roles
