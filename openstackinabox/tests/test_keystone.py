"""
Stack-In-A-Box: Basic Test
"""
import json
import unittest

import mock
import requests
import stackinabox.util_requests_mock
from stackinabox.stack import StackInABox

from openstackinabox.models.keystone.model import KeystoneModel
from openstackinabox.services.keystone import KeystoneV2Service
from openstackinabox.services.keystone.v2.users import KeystoneV2ServiceUsers
from openstackinabox.services.keystone.v2.users.byuserid import Keystonev2ServiceUsersById


class TestHttprettyKeystone(unittest.TestCase):

    def setUp(self):
        super(TestHttprettyKeystone, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }
        StackInABox.register_service(self.keystone)
        self.session = requests.Session()

    def tearDown(self):
        super(TestHttprettyKeystone, self).tearDown()
        StackInABox.reset_services()
        self.session.close()

    def test_keystone_set_model(self):
        with self.assertRaises(TypeError):
            self.keystone.model = None

        self.keystone.model = KeystoneModel()

    def test_keystone_url_matcher(self):

        positive_cases = [
            ('/users/1', '1'),
            ('/users/2/OS-KSADM/credentials', '2')
        ]

        negative_cases = [
            '/users',
            '/users/A',
            '/users/1A',
            '/users/1/OS-KSADM',
            '/users/B/OS-KSADM',
            '/users/B/OS-KSADM/credentials'
            '/users/2B/OS-KSADM/credentials'
        ]

        for case_uri, case_id in positive_cases:
            user_id = Keystonev2ServiceUsersById.get_user_id_from_path(case_uri)
            self.assertEqual(user_id, case_id)

        for case_uri in negative_cases:
            with self.assertRaises(Exception):
                Keystonev2ServiceUsersById.get_user_id_from_path(case_uri)
