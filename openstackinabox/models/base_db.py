from openstackinabox.models.base_model import BaseModel


class ModelDbBase(BaseModel):

    def __init__(self, name, master, db):
        super(ModelDbBase, self).__init__(name)
        self.__master = master
        self.__db = db

    @property
    def master(self):
        return self.__master

    @property
    def database(self):
        return self.__db

    @staticmethod
    def bool_from_database(value):
        if value:
            return True
        return False

    @staticmethod
    def bool_to_database(value):
        if value:
            return 1
        return 0

    def initialize(self, *args, **kwargs):
        raise NotImplementedError("Not Implemented By Base Model")
