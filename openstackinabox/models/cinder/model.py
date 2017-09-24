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

    CHILD_MODELS = {
    }

    @staticmethod
    def initialize_db_schema(db_instance):
        dbcursor = db_instance.cursor()
        for table_sql in schema:
            dbcursor.execute(table_sql)
        db_instance.commit()

    @classmethod
    def get_child_models(cls, instance, db_instance):
        return {
            model_name: model_type(instance, db_instance)
            for model_name, model_type in six.iteritems(cls.CHILD_MODELS)
        }

    def __init__(self, keystone_model, initialize=True):
        super(CinderModel, self).__init__('CinderModel')
        self.keystone_model = keystone_model
        self.database = sqlite3.connect(':memory:')
        self.child_models = self.get_child_models(self, self.database)
        if initialize:
            self.init_database()

    def init_database(self):
        self.log_info('Initializing database')
        self.initialize_db_schema(self.database)

        # initialize the child models here

        self.database.commit()
        self.log_info('Database initialized')
