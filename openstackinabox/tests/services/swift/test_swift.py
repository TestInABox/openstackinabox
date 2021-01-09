"""
Stack-In-A-Box: Basic Test
"""
import unittest
import uuid

import ddt
import mock
import requests
from stackinabox.services.service import StackInABoxService
from stackinabox.stack import StackInABox

from openstackinabox.services.keystone import KeystoneV2Service

from openstackinabox.models.swift.model import SwiftServiceModel
from openstackinabox.models.swift.storage import SwiftStorage
from openstackinabox.services.swift import SwiftV1Service


@ddt.ddt
class TestHttprettySwift(unittest.TestCase):

    def setUp(self):
        super(TestHttprettySwift, self).setUp()
        self.keystone = KeystoneV2Service()
        self.swift = SwiftV1Service()
        self.headers = {
            'x-auth-token': self.keystone.model.tokens.admin_token
        }
        StackInABox.register_service(self.keystone)
        StackInABox.register_service(self.swift)
        self.session = requests.Session()

    def tearDown(self):
        super(TestHttprettySwift, self).tearDown()
        StackInABox.reset_services()
        self.session.close()

    @ddt.data(
        (0, 0),
        (1, 0),
        (2, 1),
        (3, 2),
        (4, 3),
        (10, 9),
        (50, 49),
        (100, 99)
    )
    @ddt.unpack
    def test_word_matcher(self, depth, container_count):
        expected_tenant_id = '/123456'

        path = '{0}'.format(expected_tenant_id)
        last_word = None
        for ignored in range(depth):
            last_word = str(uuid.uuid4()).replace('-', '')
            path += '/{0}'.format(last_word)

        data = SwiftV1Service.URL_REGEX.match(path)
        if container_count == 0:
            self.assertIsNone(data)
        else:
            self.assertIsNotNone(data)
            data_groups = data.groups()
            self.assertEqual(
                len(data_groups),
                3
            )

            tenant_id, container_name, object_name = data_groups
            self.assertEqual(tenant_id, expected_tenant_id)

    @ddt.data(
        (0, 0),
        (1, 0),
        (2, 1),
        (3, 2),
        (4, 3),
        (10, 9),
        (50, 49),
        (100, 99)
    )
    @ddt.unpack
    def test_split_uri(self, depth, container_count):
        expected_tenant_id = '123456'

        uri = '/{0}'.format(expected_tenant_id)
        expected_object_name = None
        for ignored in range(depth):
            expected_object_name = str(uuid.uuid4()).replace('-', '')

            uri += '/{0}'.format(
                expected_object_name
            )

        expected_container = None
        if container_count:
            expected_container = uri[
                (len(expected_tenant_id) + 2):-(len(expected_object_name) + 1)
            ]

        uri_data = SwiftV1Service.split_uri(uri)
        self.assertEqual(len(uri_data), 3)

        tenant_id, container, object_name = uri_data
        if container_count == 0:
            self.assertIsNone(tenant_id)
            self.assertIsNone(container)
            self.assertIsNone(object_name)
        else:
            self.assertEqual(tenant_id, expected_tenant_id)
            self.assertEqual(container, expected_container)
            self.assertEqual(object_name, expected_object_name)

    @ddt.data(
        ("hello world", "hello world"),
        ("hello\\world", "hello world"),
        ("hello/world", "hello world"),
        ("hello\\world/perty\\cat", "hello world perty cat"),
        ("hello/world perty\\cat", "hello world perty cat")
    )
    @ddt.unpack
    def test_sanitize_name(self, name_submission, expected_name):
        self.assertEqual(
            SwiftV1Service.sanitize_name(name_submission),
            expected_name
        )

    def test_initialization(self):
        self.assertFalse(self.swift.fail_auth)
        self.assertIsNone(self.swift.fail_error_code)
        self.assertIsInstance(self.swift.model, SwiftServiceModel)
        self.assertIsInstance(self.swift.storage, SwiftStorage)

    def test_do_register_object(self):
        with mock.patch(
            'openstackinabox.services.swift.SwiftV1Service.register'
        ) as mock_stack_register:
            service = SwiftV1Service()
            tenant_id = '12345'
            container_name = 'hello'
            object_name = 'world'
            expected_uri = '/{0}/{1}/{2}'.format(
                tenant_id,
                container_name,
                object_name
            )

            expected_calls = [
                (StackInABoxService.GET, expected_uri,
                 SwiftV1Service.get_object_handler),
                (StackInABoxService.PUT, expected_uri,
                 SwiftV1Service.put_object_handler),
                (StackInABoxService.POST, expected_uri,
                 SwiftV1Service.put_object_handler),
                (StackInABoxService.HEAD, expected_uri,
                 SwiftV1Service.head_object_handler),
                (StackInABoxService.DELETE, expected_uri,
                 SwiftV1Service.delete_object_handler)
            ]

            service.do_register_object(
                tenant_id,
                container_name,
                object_name
            )

            for expected_call in expected_calls:
                mock_stack_register.assert_any_call(*expected_call)

    def test_add_transaction(self):
        with mock.patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = 'uuid'

            service = SwiftV1Service()
            headers = {}
            service.add_transaction(headers)
            self.assertIn('x-trans-id', headers)
            self.assertIn('date', headers)
            self.assertEqual('uuid', headers['x-trans-id'])
