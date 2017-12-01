from openstackinabox.models.base_model import BaseModel


class ModelDbBase(BaseModel):
    """
    Model Base for common functionality
    """

    def __init__(self, name, master, db):
        """
        :param unicode name: name of the model
        :param obj master: master model, f.e KeystoneModel
        :param sqlite3 db: Sqlite3 DB instance for storing data

        .. note:: Typically the Master Model is the Keystone Model in order
            to make it easy to do token validation, look-up accounts, etc.

        .. note:: objects are configured but full initialization is delayed
            until `initialize` is called on the object. This allows some
            testing to be done when data has not been configured.
        """
        super(ModelDbBase, self).__init__(name)
        self.__master = master
        self.__db = db

    @property
    def master(self):
        """
        Access the master model
        """
        return self.__master

    @property
    def database(self):
        """
        Access the model's database
        """
        return self.__db

    @staticmethod
    def bool_from_database(value):
        """
        Convert the value from a storable value to a boolean
        :param value: parameter to convert
        :retval: boolean
        """
        if value:
            return True
        return False

    @staticmethod
    def bool_to_database(value):
        """
        Convert the value to a storable value from a boolean
        :param value: parameter to convert
        :retval: integer
        """
        if value:
            return 1
        return 0

    def initialize(self, *args, **kwargs):
        """
        Complete the object initialize, configuring the database, etc.
        """
        raise NotImplementedError("Not Implemented By Base Model")
