import copy
import hashlib
import os
import os.path
import tempfile
import uuid

import ddt
import mock
import six
from stackinabox.util.tools import CaseInsensitiveDict

from openstackinabox.tests.base import TestBase

from openstackinabox.models.swift import exceptions
from openstackinabox.models.swift import model
from openstackinabox.models.swift import storage
from openstackinabox.utils.directory import TemporaryDirectory


class TestSwiftStorageEtag(TestBase):

    def setUp(self):
        super(TestSwiftStorageEtag, self).setUp(initialize=False)

    def tearDown(self):
        super(TestSwiftStorageEtag, self).tearDown()

    def test_get_etag(self):
        data = os.urandom(1024)
        local_hash = hashlib.md5()
        local_hash.update(data)
        expected_etag = local_hash.hexdigest()

        self.assertEqual(
            storage.SwiftStorage.get_etag(data),
            expected_etag
        )

    def test_get_file_etag(self):
        data = os.urandom(1024)
        local_hash = hashlib.md5()
        local_hash.update(data)
        expected_etag = local_hash.hexdigest()

        local_file = tempfile.NamedTemporaryFile()
        with open(local_file.name, 'wb') as output_file:
            output_file.write(data)

        self.assertEqual(
            storage.SwiftStorage.get_file_etag(local_file.name),
            expected_etag
        )


class TestSwiftStorageBase(TestBase):

    def setUp(self, initialize):
        super(TestSwiftStorageBase, self).setUp(initialize=initialize)
        self.service_id = 'abc123'
        self.model = model.SwiftServiceModel()
        self.tenant_id = '123456'
        self.tenant_path = '/{0}'.format(self.tenant_id)
        self.container_name = 'foobar'
        self.container_path = '{0}/{1}'.format(
            self.tenant_path,
            self.container_name
        )
        self.object_name = 'raboof'
        self.object_path = '{0}/{1}'.format(
            self.container_path,
            self.object_name
        )

    def tearDown(self):
        super(TestSwiftStorageBase, self).tearDown()


class TestSwiftStorageInstance(TestSwiftStorageBase):

    def setUp(self):
        super(TestSwiftStorageInstance, self).setUp(initialize=False)

    def tearDown(self):
        super(TestSwiftStorageInstance, self).tearDown()

    def test_instantiation(self):
        fake_model = 'a fake model'
        instance = storage.SwiftStorage(
            self.service_id,
            fake_model
        )
        self.assertEqual(
            instance.model,
            fake_model
        )

        instance.model = self.model

        self.assertEqual(
            id(instance.model),
            id(self.model)
        )
        self.assertTrue(os.path.exists(instance.location))
        self.assertEqual(instance.metadata, {})
        self.assertEqual(instance.custom_metadata, {})


@ddt.ddt
class TestSwiftStoragePaths(TestSwiftStorageBase):

    def setUp(self):
        super(TestSwiftStoragePaths, self).setUp(initialize=False)

        self.internal_tenant_id = self.model.add_tenant(
            self.tenant_id,
            self.tenant_path
        )
        self.internal_container_id = self.model.add_container(
            self.internal_tenant_id,
            self.container_name,
            self.container_path
        )
        self.internal_object_id = self.model.add_object(
            self.internal_tenant_id,
            self.internal_container_id,
            self.object_name,
            self.object_path
        )

    def tearDown(self):
        super(TestSwiftStoragePaths, self).tearDown()

    def test_tenant_path(self):
        instance = storage.SwiftStorage(
            self.service_id,
            self.model
        )
        tenant_path = instance.get_tenant_path(self.tenant_id)
        self.assertTrue(
            tenant_path.startswith(instance.location)
        )
        self.assertIn(self.tenant_id, tenant_path)

    def test_container_path(self):
        instance = storage.SwiftStorage(
            self.service_id,
            self.model
        )

        container_path = instance.get_container_path(
            self.tenant_id,
            self.container_name
        )

        self.assertTrue(
            container_path.startswith(
                instance.get_tenant_path(
                    self.tenant_id
                )
            )
        )
        self.assertIn(self.container_name, container_path)

    def test_object_path(self):
        instance = storage.SwiftStorage(
            self.service_id,
            self.model
        )

        object_path = instance.get_object_path(
            self.tenant_id,
            self.container_name,
            self.object_name
        )

        self.assertEqual(
            object_path,
            self.object_path
        )

    @ddt.data(
        ('tenantid', exceptions.SwiftUnknownTenantError),
        ('container_name', exceptions.SwiftUnknownContainerError),
        ('object_name', exceptions.SwiftUnknownObjectError),
    )
    @ddt.unpack
    def test_object_path_failure(self, invalid_part, exception_raised):
        instance = storage.SwiftStorage(
            self.service_id,
            self.model
        )

        with self.assertRaises(exception_raised):
            instance.get_object_path(
                self.tenant_id
                if invalid_part != 'tenantid' else 'bad',
                self.container_name
                if invalid_part != 'container_name' else 'bad',
                self.object_name
                if invalid_part != 'object_name' else 'bad',
            )


@ddt.ddt
class TestSwiftStorageTenant(TestSwiftStorageBase):

    def setUp(self):
        super(TestSwiftStorageTenant, self).setUp(initialize=False)
        self.temp_dir = TemporaryDirectory()

    def tearDown(self):
        super(TestSwiftStorageTenant, self).tearDown()

    @ddt.data(
        False,
        True
    )
    def test_has_tenant(self, has_tenant):
        instance = storage.SwiftStorage(
            self.service_id,
            self.model
        )

        if has_tenant:
            self.internal_tenant_id = self.model.add_tenant(
                self.tenant_id,
                self.temp_dir.name
            )

        self.assertEqual(
            instance.has_tenant(self.tenant_id),
            has_tenant
        )

    @ddt.data(
        False,
        True
    )
    def test_add_tenant(self, has_tenant):
        instance = storage.SwiftStorage(
            self.service_id,
            self.model
        )

        if has_tenant:
            self.internal_tenant_id = self.model.add_tenant(
                self.tenant_id,
                self.temp_dir.name
            )

        instance.add_tenant(self.tenant_id)

        if not has_tenant:
            self.assertTrue(self.model.has_tenant(self.tenant_id))


@ddt.ddt
class TestSwiftStorageContainer(TestSwiftStorageBase):

    def setUp(self):
        super(TestSwiftStorageContainer, self).setUp(initialize=False)
        self.instance = storage.SwiftStorage(
            self.service_id,
            self.model
        )
        self.tenant_dir = self.instance.get_tenant_path(self.tenant_id)
        self.container_dir = self.instance.get_container_path(
            self.tenant_id,
            self.container_name
        )

    def tearDown(self):
        super(TestSwiftStorageContainer, self).tearDown()
        self.instance.storage.cleanup()

    @ddt.data(
        False,
        True
    )
    def test_has_container(self, has_container):
        os.mkdir(self.tenant_dir)
        internal_tenant_id = self.model.add_tenant(
            self.tenant_id,
            self.tenant_dir
        )

        if has_container:
            os.mkdir(self.container_dir)
            self.model.add_container(
                internal_tenant_id,
                self.container_name,
                self.container_dir
            )

    @ddt.data(
        (False, False),
        (True, False),
        (True, True),
    )
    @ddt.unpack
    def test_add_container(self, has_tenant, has_container):
        internal_tenant_id = None
        internal_container_id = None

        if has_tenant:
            os.mkdir(self.tenant_dir)
            internal_tenant_id = self.model.add_tenant(
                self.tenant_id,
                self.tenant_dir
            )

        if has_container:
            os.mkdir(self.container_dir)
            internal_container_id = self.model.add_container(
                internal_tenant_id,
                self.container_name,
                self.container_dir
            )

        data_set = self.instance.add_container(
            self.tenant_id,
            self.container_name
        )
        self.assertEqual(len(data_set), 2)
        self.assertEqual(
            data_set[0],
            self.model.has_tenant(self.tenant_id)
        )
        self.assertEqual(
            data_set[1],
            self.model.has_container(
                data_set[0],
                self.container_name
            )
        )

        if has_tenant:
            self.assertEqual(internal_tenant_id, data_set[0])

        if has_container:
            self.assertEqual(internal_container_id, data_set[1])

    @ddt.data(
        (False, False),
        (True, False),
        (True, True),
    )
    @ddt.unpack
    def test_get_container(self, has_tenant, has_container):
        internal_tenant_id = None
        internal_container_id = None

        if has_tenant:
            internal_tenant_id = self.model.add_tenant(
                self.tenant_id,
                self.tenant_dir
            )

        if has_container:
            internal_container_id = self.model.add_container(
                internal_tenant_id,
                self.container_name,
                self.container_dir
            )

        data_set = self.instance.get_container(
            self.tenant_id,
            self.container_name
        )

        if False in (has_tenant, has_container):
            self.assertIsNone(data_set[0])
            self.assertIsNone(data_set[1])

        else:
            self.assertEqual(data_set[0], internal_tenant_id)
            self.assertEqual(data_set[1], internal_container_id)


@ddt.ddt
class TestSwiftStorageObject(TestSwiftStorageBase):

    def setUp(self):
        super(TestSwiftStorageObject, self).setUp(initialize=False)
        self.instance = storage.SwiftStorage(
            self.service_id,
            self.model
        )
        self.tenant_dir = self.instance.get_tenant_path(self.tenant_id)
        self.container_dir = self.instance.get_container_path(
            self.tenant_id,
            self.container_name
        )

        os.mkdir(self.tenant_dir)
        self.internal_tenant_id = self.model.add_tenant(
            self.tenant_id,
            self.tenant_dir
        )

        os.mkdir(self.container_dir)
        self.internal_container_id = self.model.add_container(
            self.internal_tenant_id,
            self.container_name,
            self.container_dir
        )
        self.object_path = '{0}/{1}'.format(
            self.instance.get_container_path(
                self.tenant_id,
                self.container_name
            ),
            self.object_name
        )

    def tearDown(self):
        super(TestSwiftStorageObject, self).tearDown()
        self.instance.storage.cleanup()

    def create_object_file(self, object_path, write_kilobytes):
        with open(object_path, 'w') as data_output:
            for ignored in range(write_kilobytes):
                data_output.write(str(os.urandom(1024)))

    @ddt.data(
        False,
        True
    )
    def test_has_object(self, has_object):
        if has_object:
            self.model.add_object(
                self.internal_tenant_id,
                self.internal_container_id,
                self.object_name,
                self.object_path
            )
            self.instance.get_object_path(
                self.tenant_id,
                self.container_name,
                self.object_name
            )
            self.create_object_file(self.object_path, 1)

        self.assertEqual(
            self.instance.has_object(
                self.tenant_id,
                self.container_name,
                self.object_name
            ),
            has_object
        )

    @ddt.data(
        (False, False, False),
        (False, True, False),
        (True, True, False),
        (True, False, False),
        (False, False, True),
        (False, True, True),
        (True, True, True),
        (True, False, True)
    )
    @ddt.unpack
    def test_load_object_from_file(
        self, has_container, send_file_size, allow_file_size_mismatch
    ):
        with mock.patch(
            'openstackinabox.models.swift.storage.SwiftStorage.store_object'
        ) as mock_store_object:
            container_name = (
                self.container_name
                if has_container
                else '{0}_{1}'.format(
                    self.container_name,
                    str(uuid.uuid4()).replace('-', '')
                )
            )
            object_name = str(uuid.uuid4())

            object_data_file = tempfile.NamedTemporaryFile()
            self.create_object_file(object_data_file.name, 10)

            expected_file_size = os.path.getsize(object_data_file.name)
            expected_etag = self.instance.get_file_etag(object_data_file.name)
            expected_metadata = CaseInsensitiveDict()
            expected_metadata.update(
                {
                    'content-length': str(expected_file_size),
                    'content-type': 'application/binary',
                    'etag': expected_etag
                }
            )

            file_size = (
                expected_file_size
                if send_file_size
                else None
            )

            self.instance.load_object_from_file(
                self.tenant_id,
                container_name,
                object_name,
                object_data_file.name,
                file_size=file_size,
                allow_file_size_mismatch=allow_file_size_mismatch
            )

            self.assertTrue(
                self.instance.has_container(
                    self.tenant_id,
                    container_name
                )
            )

            mock_store_object.assert_called_once()
            mso_args, mso_kwargs = mock_store_object.call_args

            self.assertEqual(mso_args[0], self.tenant_id)
            self.assertEqual(mso_args[1], container_name)
            self.assertEqual(mso_args[2], object_name)
            self.assertEqual(mso_args[4], expected_metadata)
            self.assertEqual(mso_args[5], expected_file_size)
            self.assertEqual(mso_args[6], allow_file_size_mismatch)

            self.assertTrue(hasattr(mso_args[3], 'read'))

    @ddt.data(
        (False, False, False),
        (False, True, False),
        (True, True, False),
        (True, False, False),
        (False, False, True),
        (False, True, True),
        (True, True, True),
        (True, False, True)
    )
    @ddt.unpack
    def test_load_object(
        self, has_container, send_file_size, allow_file_size_mismatch
    ):
        with mock.patch(
            'openstackinabox.models.swift.storage.SwiftStorage.store_object'
        ) as mock_store_object:
            container_name = (
                self.container_name
                if has_container
                else '{0}_{1}'.format(
                    self.container_name,
                    str(uuid.uuid4()).replace('-', '')
                )
            )
            object_name = str(uuid.uuid4())

            object_data_file = tempfile.NamedTemporaryFile()
            self.create_object_file(object_data_file.name, 10)

            with open(object_data_file.name, 'rb') as data_input:
                expected_data = data_input.read()

                expected_file_size = os.path.getsize(object_data_file.name)
                expected_etag = self.instance.get_file_etag(
                    object_data_file.name
                )
                expected_metadata = CaseInsensitiveDict()
                expected_metadata.update(
                    {
                        'content-length': str(expected_file_size),
                        'content-type': 'application/binary',
                        'etag': expected_etag
                    }
                )

                file_size = (
                    expected_file_size
                    if send_file_size
                    else None
                )

                self.instance.load_object(
                    self.tenant_id,
                    container_name,
                    object_name,
                    expected_data,
                    file_size=file_size,
                    allow_file_size_mismatch=allow_file_size_mismatch
                )

                self.assertTrue(
                    self.instance.has_container(
                        self.tenant_id,
                        container_name
                    )
                )

                mock_store_object.assert_called_once()
                mso_args, mso_kwargs = mock_store_object.call_args

                self.assertEqual(mso_args[0], self.tenant_id)
                self.assertEqual(mso_args[1], container_name)
                self.assertEqual(mso_args[2], object_name)
                self.assertEqual(mso_args[3], expected_data)
                self.assertEqual(mso_args[4], expected_metadata)
                self.assertEqual(mso_args[5], expected_file_size)
                self.assertEqual(mso_args[6], allow_file_size_mismatch)

    @ddt.data(
        False,
        True
    )
    def test_update_object_etag(self, has_path):
        object_data_file = tempfile.NamedTemporaryFile()
        self.create_object_file(object_data_file.name, 5)
        object_name = (
            self.object_name
            if has_path
            else '{0}_{1}'.format(
                self.object_name,
                str(uuid.uuid4())
            )
        )
        self.model.add_object(
            self.internal_tenant_id,
            self.internal_container_id,
            object_name,
            self.object_path
        )
        original_data_etag = self.instance.get_file_etag(
            object_data_file.name
        )
        if has_path:
            self.instance.metadata[self.object_path] = {
                'etag': original_data_etag
            }

        new_etag_value = str(uuid.uuid4())
        self.instance.update_object_etag(
            self.tenant_id,
            self.container_name,
            object_name,
            new_etag_value
        )

        if has_path:
            stored_etag_value = (
                self.instance.metadata[self.object_path]['etag']
            )
            self.assertEqual(
                stored_etag_value,
                new_etag_value
            )
        else:
            self.assertNotIn(
                self.object_path,
                self.instance.metadata
            )

    @ddt.data(
        False,
        True
    )
    def test_store_or_update_custom_metadata(self, has_path):
        object_data_file = tempfile.NamedTemporaryFile()
        self.create_object_file(object_data_file.name, 5)
        self.model.add_object(
            self.internal_tenant_id,
            self.internal_container_id,
            self.object_name,
            self.object_path
        )
        initial_metadata = {
            'master': 'database'
        }
        if has_path:
            self.instance.custom_metadata[self.object_path] = initial_metadata

        new_data = {
            'secondary': str(uuid.uuid4())
        }

        self.instance.store_or_update_custom_metadata(
            self.tenant_id,
            self.container_name,
            self.object_name,
            new_data
        )

        self.assertIn(self.object_path, self.instance.custom_metadata)
        current_metadata = self.instance.custom_metadata[self.object_path]
        expected_data = {}
        if has_path:
            expected_data = copy.deepcopy(initial_metadata)
            expected_data.update(new_data)
        else:
            expected_data = new_data

        self.assertEqual(
            current_metadata,
            expected_data
        )

    @ddt.data(
        False,
        True
    )
    def test_retrieve_custom_metadata(self, has_path):
        object_data_file = tempfile.NamedTemporaryFile()
        self.create_object_file(object_data_file.name, 5)
        self.model.add_object(
            self.internal_tenant_id,
            self.internal_container_id,
            self.object_name,
            self.object_path
        )
        initial_metadata = {
            'master': str(uuid.uuid4())
        }

        if has_path:
            self.instance.custom_metadata[self.object_path] = initial_metadata

        current_metadata = self.instance.retrieve_custom_metadata(
            self.tenant_id,
            self.container_name,
            self.object_name
        )

        if has_path:
            self.assertEqual(current_metadata, initial_metadata)
        else:
            self.assertEqual(current_metadata, CaseInsensitiveDict())

    @ddt.data(
        False,
        True
    )
    def test_remove_custom_metadata(self, has_path):
        object_data_file = tempfile.NamedTemporaryFile()
        self.create_object_file(object_data_file.name, 5)
        self.model.add_object(
            self.internal_tenant_id,
            self.internal_container_id,
            self.object_name,
            self.object_path
        )
        initial_metadata = {
            'master': str(uuid.uuid4())
        }

        if has_path:
            self.instance.custom_metadata[self.object_path] = initial_metadata

        self.instance.remove_custom_metadata(
            self.tenant_id,
            self.container_name,
            self.object_name
        )

        self.assertNotIn(self.object_path, self.instance.custom_metadata)

    @ddt.data(
        (False, False, False, ),
        (False, True, False, ),
        (True, False, False, ),
        (True, True, False, ),
        (False, False, True, ),
        (False, True, True, ),
        (True, False, True, ),
        (True, True, True, ),
    )
    @ddt.unpack
    def test_store_object(
        self, has_container, has_file_size, allow_file_size_mismatch
    ):
        container_name = (
            self.container_name
            if has_container
            else '{0}_{1}'.format(
                self.container_name,
                str(uuid.uuid4()).replace('-', '')
            )
        )

        # 2kb of random data
        content = os.urandom(2048)

        metadata = {
            'x-tenant-id': self.tenant_id,
            'x-container': self.container_name,
            'x-object': self.object_name,
            'content-length': len(content)
        }

        self.instance.store_object(
            self.tenant_id,
            container_name,
            self.object_name,
            content,
            metadata,
            file_size=(
                len(content)
                if has_file_size
                else None
            ),
            allow_file_size_mismatch=allow_file_size_mismatch
        )

        object_on_disk_path = self.instance.get_object_path(
            self.tenant_id,
            container_name,
            self.object_name
        )

        with open(object_on_disk_path, 'rb') as object_on_disk:
            data_on_disk = object_on_disk.read()
            self.assertEqual(
                data_on_disk,
                content
            )

        self.assertIn(object_on_disk_path, self.instance.metadata)

        expected_metadata = copy.deepcopy(metadata)
        expected_metadata['x-y-object-disk-path'] = object_on_disk_path
        self.assertEqual(
            self.instance.metadata[object_on_disk_path],
            expected_metadata
        )

    def test_store_object_zero_length(self):

        # 2kb of random data
        content = (
            ''
            if six.PY2
            else b''
        )

        metadata = {
            'x-tenant-id': self.tenant_id,
            'x-container': self.container_name,
            'x-object': self.object_name,
            'content-length': len(content)
        }

        self.instance.store_object(
            self.tenant_id,
            self.container_name,
            self.object_name,
            content,
            metadata,
            file_size=len(content),
            allow_file_size_mismatch=False
        )

        object_on_disk_path = self.instance.get_object_path(
            self.tenant_id,
            self.container_name,
            self.object_name
        )

        with open(object_on_disk_path, 'rb') as object_on_disk:
            data_on_disk = object_on_disk.read()
            self.assertEqual(
                data_on_disk,
                content
            )

        self.assertIn(object_on_disk_path, self.instance.metadata)

        expected_metadata = copy.deepcopy(metadata)
        expected_metadata['x-y-object-disk-path'] = object_on_disk_path
        self.assertEqual(
            self.instance.metadata[object_on_disk_path],
            expected_metadata

        )

    @ddt.data(
        False,
        True
    )
    def test_store_object_filesize_mismatch(self, allow_file_size_mismatch):
        # 2kb of random data
        content = os.urandom(2048)

        metadata = {
            'x-tenant-id': self.tenant_id,
            'x-container': self.container_name,
            'x-object': self.object_name,
            'content-length': len(content) * 2
        }

        if not allow_file_size_mismatch:
            with self.assertRaises(RuntimeError):
                self.instance.store_object(
                    self.tenant_id,
                    self.container_name,
                    self.object_name,
                    content,
                    metadata,
                    file_size=len(content),
                    allow_file_size_mismatch=allow_file_size_mismatch
                )
        else:
            self.instance.store_object(
                self.tenant_id,
                self.container_name,
                self.object_name,
                content,
                metadata,
                file_size=len(content),
                allow_file_size_mismatch=allow_file_size_mismatch
            )

            object_on_disk_path = self.instance.get_object_path(
                self.tenant_id,
                self.container_name,
                self.object_name
            )

            with open(object_on_disk_path, 'rb') as object_on_disk:
                data_on_disk = object_on_disk.read()
                self.assertEqual(
                    data_on_disk,
                    content
                )

            self.assertIn(object_on_disk_path, self.instance.metadata)

            expected_metadata = copy.deepcopy(metadata)
            expected_metadata['x-y-object-disk-path'] = object_on_disk_path
            self.assertEqual(
                self.instance.metadata[object_on_disk_path],
                expected_metadata
            )

    def test_retrieve_object_failure_1(self):
        # object not stored at all
        data, metadata = self.instance.retrieve_object(
            self.tenant_id,
            self.container_name,
            self.object_name
        )
        self.assertIsNone(data)
        self.assertIsNone(metadata)

    @mock.patch(
        'openstackinabox.models.swift.storage.SwiftStorage.get_object_path'
    )
    @mock.patch('openstackinabox.models.swift.storage.SwiftStorage.has_object')
    def test_retrieve_object_failure_2(
        self, mock_has_object, mock_get_object_path
    ):
        object_path = '/dev/null/{0}'.format(
            str(uuid.uuid4()).replace('-', '')
        )
        mock_has_object.return_value = True
        mock_get_object_path.return_value = object_path

        self.instance.metadata[object_path] = {
            'content-length': 2048
        }

        data, metadata = self.instance.retrieve_object(
            self.tenant_id,
            self.container_name,
            self.object_name
        )
        self.assertIsNone(data)

        expected_metadata = CaseInsensitiveDict()
        expected_metadata.update(metadata)

        self.assertEqual(metadata, expected_metadata)

    @ddt.data(
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    )
    @ddt.unpack
    @mock.patch(
        'openstackinabox.models.swift.storage.SwiftStorage.get_object_path'
    )
    @mock.patch('openstackinabox.models.swift.storage.SwiftStorage.has_object')
    def test_retrieve_object(
        self,
        has_custom_metadata, has_path_in_metadata,
        mock_has_object, mock_get_object_path
    ):
        temp_file = tempfile.NamedTemporaryFile()
        object_path = temp_file.name
        self.create_object_file(object_path, 2048)

        mock_has_object.return_value = True
        mock_get_object_path.side_effect = [
            object_path,
            object_path
        ]

        metadata = {
            'content-length': 2048
        }
        if has_path_in_metadata:
            self.instance.metadata[object_path] = metadata

        custom_metadata = {
            'x-custom': 'curious-one'
        }

        if has_custom_metadata:
            self.instance.custom_metadata[object_path] = custom_metadata

        result_data, result_metadata = self.instance.retrieve_object(
            self.tenant_id,
            self.container_name,
            self.object_name
        )

    @mock.patch('openstackinabox.models.swift.storage.SwiftStorage.has_object')
    def test_remove_object_no_object(self, mock_has_object):
        mock_has_object.return_value = False
        self.instance.remove_object(
            self.tenant_id,
            self.container_name,
            self.object_name
        )

    @mock.patch(
        'openstackinabox.models.swift.storage.SwiftStorage.get_object_path'
    )
    @mock.patch('openstackinabox.models.swift.storage.SwiftStorage.has_object')
    @mock.patch('os.remove')
    def test_remove_object(
        self, mock_os_remove, mock_has_object, mock_get_object_path
    ):
        object_data_file = tempfile.NamedTemporaryFile()
        self.create_object_file(object_data_file.name, 5)
        self.model.add_object(
            self.internal_tenant_id,
            self.internal_container_id,
            self.object_name,
            self.object_path
        )

        mock_has_object.return_value = True
        mock_get_object_path.return_value = object_data_file.name

        self.instance.remove_object(
            self.tenant_id,
            self.container_name,
            self.object_name
        )

        mock_os_remove.assert_called()
