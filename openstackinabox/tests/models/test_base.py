import mock

import ddt

from openstackinabox.tests.base import TestBase

from openstackinabox.models import base_model


@ddt.ddt
class TestBaseModel(TestBase):

    def setUp(self):
        super(TestBaseModel, self).setUp()
        self.model = base_model.BaseModel

    def tearDown(self):
        super(TestBaseModel, self).tearDown()

    def test_model_initialization(self):
        name = 'Oasirus'
        instance = self.model(name)
        self.assertEqual(name, instance.name)

    @ddt.data(
        ("log_debug", "debug"),
        ("log_info", "info"),
        ("log_exception", "exception"),
        ("log_error", "error")
    )
    @ddt.unpack
    def test_model_logging(self, log_method, mock_method):
        with mock.patch(
            'openstackinabox.models.base_model.logger'
        ) as mock_logger:
            instance = self.model('logTester')
            log_fn = getattr(instance, log_method)

            log_message = "the never-ending trial of time"
            log_fn(log_message)

            mock_fn = getattr(mock_logger, mock_method)
            mock_fn.assert_called()
