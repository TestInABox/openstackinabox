import os
import os.path

import ddt
import mock

from openstackinabox.tests.base import TestBase

from openstackinabox.utils import directory


@ddt.ddt
class TestTempDirectory(TestBase):

    def setUp(self):
        super(TestTempDirectory, self).setUp()

    def tearDown(self):
        super(TestTempDirectory, self).tearDown()

    def test_initialization(self):
        temp_dir = directory.TemporaryDirectory()
        self.assertIsInstance(temp_dir.name, str)
        self.assertIn(directory.TemporaryDirectory.__name__, repr(temp_dir))

    def test_cleanup(self):
        temp_dir = directory.TemporaryDirectory()

        self.assertTrue(os.path.exists(temp_dir.name))

        file_names = [temp_dir.name]
        for x in range(10):
            filename = '{0}/file_{1}'.format(
                temp_dir.name,
                x
            )
            with open(filename, 'w') as data_output:
                data_output.write(str(os.urandom(8192)))

            file_names.append(filename)

        temp_dir.cleanup()

        for name in file_names:
            self.assertFalse(os.path.exists(name))

    def test_del_cleanup_error(self):
        with mock.patch(
            'shutil.rmtree'
        ) as mock_rmtree:
            mock_rmtree.side_effect = OSError('mock error')

            temp_dir = directory.TemporaryDirectory()
            temp_dir.cleanup()

    def test_context(self):
        temp_dir_name = None

        temp_dir = directory.TemporaryDirectory()
        with temp_dir as context:
            self.assertEqual(id(temp_dir), id(context))
            temp_dir_name = context.name

            self.assertTrue(os.path.exists(temp_dir_name))

        try:
            self.assertFalse(os.path.exists(temp_dir_name))
        except OSError:
            pass
