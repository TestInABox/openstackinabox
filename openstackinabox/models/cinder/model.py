import sqlite3

import six

from openstackinabox.models import base_model


schema = [
    '''
        CREATE TABLE cinder_volume_types
        (
            typeid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            extra_specs TEXT
        )
    '''
]


class CinderModel(base_model.BaseModel):
    """
    OpenStack Cinder Model for the OpenStack-In-A-Box Cinder Service

    :cvar list CHILD_MODELS: list of any child models to be instantiated
        as part of the object.

    .. note:: The CHILD_MODELS are useful for splitting up functionality
        into a series of modules for better supportability.
    """

    CHILD_MODELS = {
    }

    @staticmethod
    def initialize_db_schema(db_instance):
        """
        Initialize the database with the model schema

        :param sqlite3 db_instance: Sqlite3 DB Instance Object
        """
        dbcursor = db_instance.cursor()
        for table_sql in schema:
            dbcursor.execute(table_sql)
        db_instance.commit()

    @classmethod
    def get_child_models(cls, instance, db_instance):
        """
        Retrieve the initialized child models

        :param base_model.BaseModel instance: primary model instance
        :param sqltie3 db_instance: Sqlite3 database for storing the model data
        :retval: list of base_model.BaseModel instances that make
            up the remainder of the model.

        .. note:: The model and child models all share the same database
            instance so that the information can be validated easily.
        """
        return {
            model_name: model_type(instance, db_instance)
            for model_name, model_type in six.iteritems(cls.CHILD_MODELS)
        }

    def __init__(self, keystone_model, initialize=True):
        """
        :param KeystoneModel keystone_model: Keystone Model to use for user
            data
        :param boolean initialize: whether or not to intialize the underlying
            data (e.g database); useful to delay initialization at times.
        """
        super(CinderModel, self).__init__('CinderModel')
        self.keystone_model = keystone_model
        self.database = sqlite3.connect(':memory:')
        self.child_models = self.get_child_models(self, self.database)
        if initialize:
            self.init_database()

    def init_database(self):
        """
        Initialize the model's database
        """
        self.log_info('Initializing database')
        self.initialize_db_schema(self.database)

        # initialize the child models here

        self.database.commit()
        self.log_info('Database initialized')
