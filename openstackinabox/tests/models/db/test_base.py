import ddt

from openstackinabox.tests.base import TestBase

from openstackinabox.models import base_db


@ddt.ddt
class TestModelBaseDb(TestBase):

    def setUp(self):
        super(TestModelBaseDb, self).setUp()
        self.model = base_db.ModelDbBase

    def tearDown(self):
        super(TestModelBaseDb, self).tearDown()

    def test_model_initialization(self):
        name = 'Ra'
        master = 'Omicron'
        db = 'Heroditus'

        instance = self.model(name, master, db)
        self.assertEqual(name, instance.name)
        self.assertEqual(master, instance.master)
        self.assertEqual(db, instance.database)

    @ddt.data(
        (1, True),
        (0, False)
    )
    @ddt.unpack
    def test_bool_from_database(self, value, expected_value):
        self.assertEqual(
            self.model.bool_from_database(value),
            expected_value
        )

    @ddt.data(
        (True, 1),
        (False, 0)
    )
    @ddt.unpack
    def test_bool_to_database(self, value, expected_value):
        self.assertEqual(
            self.model.bool_to_database(value),
            expected_value
        )

    def test_initialize_model(self):
        with self.assertRaises(NotImplementedError):
            instance = self.model(
                'Ulysses',
                'S',
                'Grant'
            )
            instance.initialize()
