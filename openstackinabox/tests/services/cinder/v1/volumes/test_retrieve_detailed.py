"""
"""
import unittest

import ddt
import requests
import stackinabox.util.requests_mock.core
from stackinabox.stack import StackInABox

from openstackinabox.services.cinder import CinderV1Service
from openstackinabox.services.keystone import KeystoneV2Service


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

    @ddt.data(
        ('POST', 'http://localhost/cinder/v1/volumes'),
        ('GET', 'http://localhost/cinder/v1/volumes'),
        ('GET', 'http://localhost/cinder/v1/volumes/detail'),
        ('PUT', 'http://localhost/cinder/v1/volumes/12348789'),
        ('DELETE', 'http://localhost/cinder/v1/volumes/12348789'),
    )
    @ddt.unpack
    def test_volume_not_implemented(self, verb, url):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            res = requests.request(
                verb,
                url,
                headers=self.headers
            )
            self.assertEqual(res.status_code, 500)

    def test_volume_specific_detailed_no_token(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            res = requests.get(
                'http://localhost/cinder/v1/volumes/12348789',
            )
            self.assertEqual(res.status_code, 403)

    def test_volume_specific_detailed_bad_volume_id(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            res = requests.get(
                'http://localhost/cinder/v1/volumes/_12348789',
                headers=self.headers
            )
            self.assertEqual(res.status_code, 400)

    def test_volume_specific_detailed(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            res = requests.get(
                'http://localhost/cinder/v1/volumes/12348789',
                headers=self.headers
            )
            self.assertEqual(res.status_code, 200)
