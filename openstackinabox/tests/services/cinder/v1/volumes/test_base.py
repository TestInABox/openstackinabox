"""
"""
import unittest

import ddt
from stackinabox.stack import StackInABox

from openstackinabox.models.cinder import model
from openstackinabox.services.cinder import CinderV1Service
from openstackinabox.services.keystone import KeystoneV2Service
from openstackinabox.services.keystone.v2 import exceptions


@ddt.ddt
class TestCinderV1Retrieve(unittest.TestCase):

    def setUp(self):
        super(TestCinderV1Retrieve, self).setUp()
        self.keystone = KeystoneV2Service()
        self.cinder = CinderV1Service(self.keystone)
        self.headers = {
            'x-auth-token': self.keystone.model.tokens.admin_token
        }
        StackInABox.register_service(self.keystone)
        StackInABox.register_service(self.cinder)

    def tearDown(self):
        super(TestCinderV1Retrieve, self).tearDown()
        StackInABox.reset_services()

    def test_make_volume_id(self):
        self.assertIsInstance(CinderV1Service.make_volume_id(), str)

    def test_model_access(self):
        self.assertIsNotNone(self.cinder.model)
        self.assertIsInstance(self.cinder.model, model.CinderModel)

    def test_model_set_bad_model_type(self):
        with self.assertRaises(TypeError):
            self.cinder.model = self.keystone

    def test_model_set(self):
        self.cinder.model = model.CinderModel(self.keystone.model)

    def test_helper_validate_token_no_header(self):
        with self.assertRaises(exceptions.KeystoneV2AuthForbiddenError):
            self.cinder.helper_validate_token({}, False, False)

    def test_helper_validate_token_invalid_token(self):
        headers = {
            'x-auth-token': 'hello'
        }
        with self.assertRaises(exceptions.KeystoneV2AuthUnauthorizedError):
            self.cinder.helper_validate_token(headers, False, False)

    @ddt.data(
        (False, True),
        (True, False)
    )
    @ddt.unpack
    def test_helper_validate_token_admins(
        self, enforce_admin, enforce_service
    ):
        headers = {
            'x-auth-token': self.keystone.model.tokens.admin_token
        }
        # TODO: make this better
        self.cinder.helper_validate_token(
            headers, enforce_admin, enforce_service
        )

    def test_helper_authenticate_token_no_header(self):
        result = self.cinder.helper_authenticate({}, {}, False, False)
        self.assertEqual(result[0], 403)
        self.assertEqual(result[2], 'Forbidden')

    def test_helper_authenticate_token_invalid_token(self):
        headers = {
            'x-auth-token': 'hello'
        }
        result = self.cinder.helper_authenticate(headers, {}, False, False)
        self.assertEqual(result[0], 401)
        self.assertEqual(result[2], 'Not Authorized')
