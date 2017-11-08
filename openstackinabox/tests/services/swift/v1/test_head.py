"""
Stack-In-A-Box: Basic Test
"""
import os
import unittest

import requests
import stackinabox.util.requests_mock.core
from stackinabox.stack import StackInABox

from openstackinabox.services.swift import SwiftV1Service
from openstackinabox.services.keystone import KeystoneV2Service


class TestSwiftV1ObjectHead(unittest.TestCase):

    def setUp(self):
        super(TestSwiftV1ObjectHead, self).setUp()
        self.keystone = KeystoneV2Service()
        self.swift = SwiftV1Service()
        self.headers = {
            'x-auth-token': self.keystone.model.tokens.make_token()
        }
        StackInABox.register_service(self.keystone)
        StackInABox.register_service(self.swift)

        self.tenant_id = '12345'
        self.container = 'container'
        self.object_name = 'object_name'

    def tearDown(self):
        super(TestSwiftV1ObjectHead, self).tearDown()
        StackInABox.reset_services()

    def make_url(self, tenant_id=None, container=None, object_name=None):
        return (
            'http://localhost/swift/v1.0/{0}/{1}/{2}'.format(
                self.tenant_id if tenant_id is None else tenant_id,
                self.container if container is None else container,
                self.object_name if object_name is None else object_name
            )
        )

    def register_tenant(self, tenant_id=None, path=None):
        return self.swift.storage.add_tenant(
            self.tenant_id
            if tenant_id is None
            else tenant_id
        )

    def register_container(self, tenant_id=None, container=None):
        return self.swift.storage.add_container(
            self.tenant_id
            if tenant_id is None
            else tenant_id,
            self.container
            if container is None
            else container
        )

    def register_object(
        self, tenant_id=None, container=None, object_name=None, content=None,
        metadata=None, file_size=None, allow_file_size_mismatch=False
    ):
        return self.swift.storage.store_object(
            self.tenant_id
            if tenant_id is None
            else tenant_id,
            self.container
            if container is None
            else container,
            self.object_name
            if object_name is None
            else object_name,
            content,
            {}
            if metadata is None
            else metadata,
            file_size=file_size,
            allow_file_size_mismatch=allow_file_size_mismatch
        )

    def test_auth_failure(self):
        self.swift.fail_auth = True
        self.swift.do_register_object(
            self.tenant_id,
            self.container,
            self.object_name
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            res = requests.head(self.make_url())
            self.assertEqual(res.status_code, 401)

    def test_defined_failure(self):
        self.swift.fail_error_code = 499
        self.swift.do_register_object(
            self.tenant_id,
            self.container,
            self.object_name
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            res = requests.head(self.make_url(), headers=self.headers)
            self.assertEqual(res.status_code, 499)

    def test_object_not_found(self):
        self.swift.do_register_object(
            self.tenant_id,
            self.container,
            self.object_name
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            res = requests.head(self.make_url(), headers=self.headers)
            self.assertEqual(res.status_code, 404)

    def test_zero_length_file(self):
        self.swift.do_register_object(
            self.tenant_id,
            self.container,
            self.object_name
        )
        self.register_tenant()
        self.register_object(
            content='',
            file_size=0,
            metadata={
                'content-length': '0'
            }
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            res = requests.head(
                self.make_url(),
                headers=self.headers
            )
            self.assertEqual(res.status_code, 204)

    def test_nonzero_length_file(self):
        object_size = 1024
        object_data = os.urandom(object_size)
        self.swift.do_register_object(
            self.tenant_id,
            self.container,
            self.object_name
        )
        self.register_tenant()
        self.register_object(
            content=object_data,
            file_size=object_size,
            metadata={
                'content-length': '{0}'.format(object_size)
            }
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            res = requests.head(
                self.make_url(),
                headers=self.headers
            )
            self.assertEqual(res.status_code, 204)
            content = res.content
            self.assertEqual(len(content), 0)
