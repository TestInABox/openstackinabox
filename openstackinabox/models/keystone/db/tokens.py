import datetime
import uuid

from openstackinabox.models.keystone import exceptions

from openstackinabox.models.keystone.db.base import KeystoneDbBase


class UtcTimezone(datetime.tzinfo):

    def _offset(self):
        return datetime.timedelta(0)

    def utcoffset(self, dt):
        return self._offset()

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return self._offset()


SQL_INSERT_TOKEN = '''
    INSERT INTO keystone_tokens
    (tenantid, userid, token, ttl, revoked)
    VALUES(:tenant_id, :user_id, :token, DATETIME('NOW', '+12 HOURS'), 0)
'''

SQL_INSERT_TOKEN_AND_EXPIRATION = '''
    INSERT INTO keystone_tokens
    (tenantid, userid, token, ttl, revoked)
    VALUES(:tenant_id, :user_id, :token, :ttl, 0)
'''

SQL_GET_TOKEN_BY_TENANT_ID = '''
    SELECT tenantid, userid, token, ttl, revoked
    FROM keystone_tokens
    WHERE tenantid = :tenant_id
'''

SQL_GET_TOKEN_BY_USER_ID = '''
    SELECT tenantid, userid, token, ttl, revoked
    FROM keystone_tokens
    WHERE userid = :user_id
'''

SQL_GET_TOKEN_BY_USER_NAME = '''
    SELECT keystone_tokens.tenantid, keystone_tokens.userid,
           keystone_tokens.token, keystone_tokens.ttl, keystone_tokens.revoked
    FROM keystone_tokens, keystone_users
    WHERE keystone_tokens.tenantid = keystone_users.tenantid
      AND keystone_tokens.userid = keystone_users.userid
      AND keystone_users.username = :username
'''

SQL_REVOKE_TOKEN = '''
    UPDATE keystone_tokens
    SET revoked = 1
    WHERE tenantid = :tenant_id
      AND userid = :user_id
      AND token = :token
'''

SQL_RESET_REVOKED_TOKEN = '''
    UPDATE keystone_tokens
    SET revoked = 0
    WHERE tenantid = :tenant_id
      AND userid = :user_id
      AND token = :token
'''

SQL_DELETE_TOKEN = '''
    DELETE FROM keystone_tokens
    WHERE tenantid = :tenant_id
      AND userid = :user_id
      AND token = :token
'''

SQL_DELETE_ALL_TOKENS = '''
    DELETE FROM keystone_tokens
    WHERE tenantid = :tenant_id
      AND userid = :user_id
'''

SQL_VALIDATE_TOKEN = '''
    SELECT tenantid, userid, token, ttl, revoked
    FROM keystone_tokens
    WHERE token = :token
'''


class KeystoneDbTokens(KeystoneDbBase):

    '''2015-02-03 02:31:17'''
    EXPIRE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, master, db):
        super(KeystoneDbTokens, self).__init__("KeystoneTokens", master, db)
        self.__admin_token = None

    def initialize(self):
        self.__admin_token = 'adminstrate_with_this_{0}'.format(uuid.uuid4())

    @property
    def admin_token(self):
        return self.__admin_token

    @staticmethod
    def convert_to_utc(dt):
        if dt.utcoffset() is not None:
            return dt.replace(tzinfo=UtcTimezone())
        else:
            return dt

    def add(self, tenant_id=None, user_id=None,
            expire_time=None, token=None):
        if token is None:
            token = self.make_token()

        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'token': str(token)
        }
        if expire_time is not None:
            if not isinstance(expire_time, datetime.datetime):
                raise TypeError(
                    'expire_time must be a datetime.datetime object')

            utc_expire_time = self.convert_to_utc(expire_time)
            args['ttl'] = utc_expire_time.strftime(self.EXPIRE_TIME_FORMAT)
            dbcursor.execute(SQL_INSERT_TOKEN_AND_EXPIRATION, args)
        else:
            dbcursor.execute(SQL_INSERT_TOKEN, args)

        if not dbcursor.rowcount:
            raise exceptions.KeystoneTokenError('Unable to add token')

        self.database.commit()
        return token

    def revoke(self, tenant_id=None, user_id=None, token=None, reset=False):
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'token': token
        }
        if reset:
            dbcursor.execute(SQL_RESET_REVOKED_TOKEN, args)
        else:
            dbcursor.execute(SQL_REVOKE_TOKEN, args)

        if not dbcursor.rowcount:
            raise exceptions.KeystoneTokenError(
                'Unknown tenant_id or  user_id; or no associated token')

        self.database.commit()

    def delete(self, tenant_id=None, user_id=None, token=None):
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id,
            'user_id': user_id,
        }
        query = SQL_DELETE_ALL_TOKENS
        if token is not None:
            query = SQL_DELETE_TOKEN
            args['token'] = token
        dbcursor.execute(query, args)

        if not dbcursor.rowcount:
            raise exceptions.KeystoneTokenError(
                'Unknown tenant_id or  user_id; or no associated token')

        self.database.commit()

    def get_by_user_id(self, user_id=None):
        dbcursor = self.database.cursor()
        args = {
            'user_id': user_id
        }
        dbcursor.execute(SQL_GET_TOKEN_BY_USER_ID, args)
        token_data = dbcursor.fetchone()
        if token_data is None:
            raise exceptions.KeystoneUnknownUserError(
                'Unknown user_id - {0}'.format(user_id)
            )

        return {
            'tenant_id': token_data[0],
            'user_id': token_data[1],
            'token': token_data[2],
            'expires': token_data[3],
            'revoked': self.bool_from_database(token_data[4])
        }

    def get_by_tenant_id(self, tenant_id):
        dbcursor = self.database.cursor()
        args = {
            'tenant_id': tenant_id
        }
        return [
            {
                'tenant_id': token_data[0],
                'user_id': token_data[1],
                'token': token_data[2],
                'expires': token_data[3],
                'revoked': self.bool_from_database(token_data[4])
            }
            for token_data in dbcursor.execute(
                SQL_GET_TOKEN_BY_TENANT_ID, args
            )
        ]

    def get_by_username(self, username=None):
        dbcursor = self.database.cursor()
        args = {
            'username': username
        }
        dbcursor.execute(SQL_GET_TOKEN_BY_USER_NAME, args)
        token_data = dbcursor.fetchone()
        if token_data is None:
            raise exceptions.KeystoneUnknownUserError('Unknown username')

        return {
            'tenant_id': token_data[0],
            'user_id': token_data[1],
            'token': token_data[2],
            'expires': token_data[3],
            'revoked': self.bool_from_database(token_data[4])
        }

    @classmethod
    def check_expiration(cls, token):
        if token['revoked']:
            raise exceptions.KeystoneRevokedTokenError('Token was revoked')

        # 2015-02-03 02:30:58
        expire_time = datetime.datetime.strptime(token['expires'],
                                                 cls.EXPIRE_TIME_FORMAT)
        now = datetime.datetime.utcnow()
        if expire_time < now:
            raise exceptions.KeystoneExpiredTokenError(
                'Token expired ({0} >= {1})'.format(
                    expire_time, now
                )
            )

    def validate_token(self, token):
        dbcursor = self.database.cursor()
        args = {
            'token': token
        }
        dbcursor.execute(SQL_VALIDATE_TOKEN, args)
        token_data = dbcursor.fetchone()
        if token_data is None:
            raise exceptions.KeystoneInvalidTokenError('Invalid token')

        result = {
            'tenantid': token_data[0],
            'userid': token_data[1],
            'token': token_data[2],
            'expires': token_data[3],
            'revoked': self.bool_from_database(token_data[4])
        }
        # side-effects if token revoked or expired
        self.check_expiration(result)

        return result
