import mock

import ddt
import six

from openstackinabox.tests.base import TestBase

from openstackinabox.models.cinder.model import (
    schema,
    CinderModel
)


@ddt.ddt
class TestCinderModel(TestBase):

    def setUp(self):
        super(TestCinderModel, self).setUp()
        self.model = CinderModel
        self.cinder_model = self.model(self.master_model, initialize=False)

    def tearDown(self):
        super(TestCinderModel, self).tearDown()

    def test_initialize_db_schema(self):
        db_cursor = mock.MagicMock()
        db_execute = mock.MagicMock()
        db_commit = mock.MagicMock()
        db_instance = mock.MagicMock()
        db_instance.cursor.return_value = db_cursor
        db_instance.commit = db_commit
        db_cursor.execute = db_execute

        self.model.initialize_db_schema(db_instance)
        self.assertTrue(db_instance.cursor.called)
        self.assertTrue(db_execute.called)
        self.assertTrue(db_commit.called)
        self.assertEqual(db_execute.call_count, len(schema))
        for s in schema:
            db_execute.assert_any_call(s)

    def test_get_child_models(self):
        master = 'alpha'
        db = 'omega'

        child_models = self.model.get_child_models(master, db)
        self.assertEqual(len(child_models), len(self.model.CHILD_MODELS))

        def assert_has_instance(model_name, model_class):
            for cm_name, cm_instance in six.iteritems(child_models):
                if isinstance(cm_instance, model_class):
                    return
            self.assertFalse(
                True,
                msg="instance of {0} ({1}) not in list".format(
                    model_name,
                    model_class
                )
            )

        for child_model_name, child_model_type in six.iteritems(
            self.model.CHILD_MODELS
        ):
            assert_has_instance(child_model_name, child_model_type)

    def test_initialization(self):
        # check pre-initialization data
        self.assertEqual(
            id(self.master_model),
            id(self.cinder_model.keystone_model)
        )
        self.assertNotEqual(
            id(self.master_model.database),
            id(self.cinder_model.database)
        )
        self.assertEqual(
            len(self.cinder_model.child_models),
            len(self.model.CHILD_MODELS)
        )
        self.cinder_model.init_database()

        # check post-initialization data

    def test_full_initialization(self):
        new_model = self.model(self.master_model, initialize=True)
        self.assertEqual(
            id(self.master_model),
            id(new_model.keystone_model)
        )
        self.assertNotEqual(
            id(self.master_model.database),
            id(new_model.database)
        )
        self.assertEqual(
            len(self.cinder_model.child_models),
            len(new_model.CHILD_MODELS)
        )
