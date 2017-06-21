import unittest

import ddt
import six

from openstackinabox.tests.base import TestBase

from openstackinabox.models.keystone.db.base import KeystoneDbBase


@ddt.ddt
class TestKeystoneDbBase(TestBase):

    def setUp(self):
        super(TestKeystoneDbBase, self).setUp()
        self.model = KeystoneDbBase
        self.name = 'Jupiter'
        self.master = 'Zeus'
        self.db = 'Josephus'

    def tearDown(self):
        super(TestKeystoneDbBase, self).tearDown()

    def test_initialization(self):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertEqual(self.name, instance.name)
        self.assertEqual(self.master, instance.master)
        self.assertEqual(self.db, instance.database)

    def test_make_token(self):
        token = self.model.make_token()
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

    @ddt.data(
        ("AlphaBetaGamma", True),
        ("0293DeltaOmega", False)
    )
    @ddt.unpack
    def test_validate_username(self, value, expected_result):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertEqual(
            instance.validate_username(value),
            expected_result
        )

    @ddt.data(
        ("AlphaBetaGamma", True),
        ("0293DeltaOmega", False)
    )
    @ddt.unpack
    def test_validate_tenant_name(self, value, expected_result):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertEqual(
            instance.validate_tenant_name(value),
            expected_result
        )

    @ddt.data(
        (392834, True),
        ("392834", False),
        (39.2834, False),
        ("0293DeltaOmega", False)
    )
    @ddt.unpack
    def test_validate_tenant_id(self, value, expected_result):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertEqual(
            instance.validate_tenant_id(value),
            expected_result
        )

    @ddt.data(
        ('aT3', True),
        ('a', False),
        ('aT', False)
    )
    @ddt.unpack
    def test_validate_password(self, value, expected_result):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertEqual(
            instance.validate_password(value),
            expected_result
        )

    @ddt.data(
        (9393, False),
        ('omicron5'.encode('utf-8').decode('utf-8'), True)
    )
    @ddt.unpack
    def test_validate_apikey(self, value, expected_result):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertEqual(
            instance.validate_apikey(value),
            expected_result
        )

    @unittest.skipIf(six.PY2, "not valid for Python 2")
    def test_validate_apikey_py3(self):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertFalse(
            instance.validate_apikey(bytes('albatross', 'utf-8'))
        )

    @ddt.data(
        (9393, False),
        ('omicron5'.encode('utf-8').decode('utf-8'), True)
    )
    @ddt.unpack
    def test_validate_token(self, value, expected_result):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertEqual(
            instance.validate_token(value),
            expected_result
        )

    @unittest.skipIf(six.PY2, "not valid for Python 2")
    def test_validate_token_py3(self):
        instance = self.model(
            self.name,
            self.master,
            self.db
        )
        self.assertFalse(
            instance.validate_token(bytes('albatross', 'utf-8'))
        )
