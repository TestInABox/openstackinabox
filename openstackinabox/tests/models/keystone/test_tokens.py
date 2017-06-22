import datetime
import mock
import uuid

import ddt

from openstackinabox.tests.base import TestBase, DbFailure

from openstackinabox.models.keystone import exceptions
from openstackinabox.models.keystone.db.tokens import (
    KeystoneDbTokens,
    UtcTimezone
)


@ddt.ddt
class TestKeystoneDbTokens(TestBase):

    def setUp(self):
        super(TestKeystoneDbTokens, self).setUp(initialize=False)
        self.model = KeystoneDbTokens
        self.db = self.master_model.database
        from openstackinabox.models.keystone.model import KeystoneModel
        KeystoneModel.initialize_db_schema(self.master_model.database)
        self.master_model.roles.initialize()
        self.master_model.tenants.initialize()
        self.master_model.users.initialize()

    def tearDown(self):
        super(TestKeystoneDbTokens, self).tearDown()

    def test_initialization(self):
        instance = self.model(
            self.master_model,
            self.db
        )
        self.assertEqual(id(self.master_model), id(instance.master))
        self.assertEqual(self.db, instance.database)
        self.assertIsNone(instance.admin_token)

        instance.initialize()
        self.assertIsNotNone(instance.admin_token)

    def test_add_failure(self):
        instance = self.model(
            self.master_model,
            DbFailure(),
        )
        with self.assertRaises(TypeError):
            instance.add(
                tenant_id=123456789,
                user_id=987654321,
                expire_time='Howdy'
            )

        with self.assertRaises(exceptions.KeystoneTokenError):
            instance.add(
                tenant_id=123456789,
                user_id=987654321
            )

    def test_get_by_user_id_failure(self):
        instance = self.model(
            self.master_model,
            DbFailure(),
        )

        with self.assertRaises(exceptions.KeystoneUnknownUserError):
            instance.get_by_user_id(
                user_id=987654321
            )

    def test_get_by_username_failure(self):
        instance = self.model(
            self.master_model,
            DbFailure()
        )

        with self.assertRaises(exceptions.KeystoneUnknownUserError):
            instance.get_by_username(
                username='poseidon'
            )

    def test_revoke_failure(self):
        instance = self.model(
            self.master_model,
            DbFailure()
        )

        with self.assertRaises(exceptions.KeystoneTokenError):
            instance.revoke(
                tenant_id=123456789,
                user_id=987654321,
                token='hippie-dogs',
                reset=False
            )

    def test_delete_failure(self):
        instance = self.model(
            self.master_model,
            DbFailure(),
        )

        with self.assertRaises(exceptions.KeystoneTokenError):
            instance.delete(
                tenant_id=123456789,
                user_id=987654321,
                token='hippie-dogs'
            )

    @ddt.data(
        None,
        UtcTimezone()
    )
    def test_time_conversion(self, tzinfo):
        dt = datetime.datetime.now(tzinfo)
        dt2 = self.model.convert_to_utc(dt)
        self.assertEqual(dt, dt2)
        if tzinfo is not None:
            self.assertEqual(dt.tzname(), dt2.tzname())

    @ddt.data(
        (None, None),
        (None, datetime.datetime.utcnow()),
        (str(uuid.uuid4()), None),
        (str(uuid.uuid4()), datetime.datetime.utcnow())
    )
    @ddt.unpack
    def test_add_and_get(self, token, expire_time):
        instance = self.model(
            self.master_model,
            self.db
        )

        tenant_id = self.master_model.tenants.add(
            tenant_name='Neptune',
            description='gods of the sea',
            enabled=True
        )
        user_id = self.master_model.users.add(
            tenant_id=tenant_id,
            username='posiedon',
            email='posie@don.sea',
            password='trident',
            apikey='0v3rThr0wZ3u$',
            enabled=True
        )
        generated_token = instance.add(
            tenant_id=tenant_id,
            user_id=user_id,
            expire_time=expire_time,
            token=token
        )
        self.assertIsNotNone(generated_token)

        user_token = instance.get_by_user_id(
            user_id=user_id
        )
        self.assertEqual(user_token['tenant_id'], tenant_id)
        self.assertEqual(user_token['user_id'], user_id)
        self.assertEqual(user_token['token'], generated_token)
        if expire_time is not None:
            self.assertEqual(
                user_token['expires'],
                expire_time.strftime(self.model.EXPIRE_TIME_FORMAT)
            )
        self.assertFalse(user_token['revoked'])

        instance.revoke(
            tenant_id=tenant_id,
            user_id=user_id,
            token=generated_token,
            reset=False
        )
        user_token_updated = instance.get_by_user_id(
            user_id=user_id
        )
        self.assertTrue(user_token_updated['revoked'])
        self.assertEqual(user_token_updated['tenant_id'], tenant_id)
        self.assertEqual(user_token_updated['user_id'], user_id)
        self.assertEqual(user_token_updated['token'], generated_token)
        if expire_time is not None:
            self.assertEqual(
                user_token_updated['expires'],
                expire_time.strftime(self.model.EXPIRE_TIME_FORMAT)
            )

        instance.revoke(
            tenant_id=tenant_id,
            user_id=user_id,
            token=generated_token,
            reset=True
        )
        user_token_restored = instance.get_by_user_id(
            user_id=user_id
        )
        self.assertEqual(user_token_restored, user_token)

    @ddt.data(
        True,
        False
    )
    def test_add_and_delete(self, specify_token):
        instance = self.model(
            self.master_model,
            self.db
        )

        tenant_id = self.master_model.tenants.add(
            tenant_name='Neptune',
            description='gods of the sea',
            enabled=True
        )
        user_id = self.master_model.users.add(
            tenant_id=tenant_id,
            username='posiedon',
            email='posie@don.sea',
            password='trident',
            apikey='0v3rThr0wZ3u$',
            enabled=True
        )
        generated_token = instance.add(
            tenant_id=tenant_id,
            user_id=user_id,
        )
        self.assertIsNotNone(generated_token)

        instance.get_by_user_id(
            user_id=user_id
        )

        kwargs = {
            'tenant_id': tenant_id,
            'user_id': user_id
        }
        if specify_token:
            kwargs['token'] = generated_token

        instance.delete(
            **kwargs
        )

        with self.assertRaises(exceptions.KeystoneUnknownUserError):
            instance.get_by_user_id(
                user_id=user_id
            )

    @ddt.data(
        0,
        1,
        5
    )
    def test_get_by_tenant_id(self, token_count):
        instance = self.model(
            self.master_model,
            self.db
        )

        tenant_id = self.master_model.tenants.add(
            tenant_name='Neptune',
            description='gods of the sea',
            enabled=True
        )
        user_id = self.master_model.users.add(
            tenant_id=tenant_id,
            username='posiedon',
            email='posie@don.sea',
            password='trident',
            apikey='0v3rThr0wZ3u$',
            enabled=True
        )
        generated_tokens = [
            instance.add(
                tenant_id=tenant_id,
                user_id=user_id,
            )
            for ignored in range(token_count)
        ]

        retrieved_token_data = [
            token_data
            for token_data in instance.get_by_tenant_id(tenant_id)
        ]

        self.assertEqual(len(generated_tokens), len(retrieved_token_data))
        for token_data in retrieved_token_data:
            self.assertEqual(token_data['tenant_id'], tenant_id)
            self.assertEqual(token_data['user_id'], user_id)
            self.assertIn(token_data['token'], generated_tokens)

    def test_get_by_username(self):
        instance = self.model(
            self.master_model,
            self.db
        )

        tenant_id = self.master_model.tenants.add(
            tenant_name='Neptune',
            description='gods of the sea',
            enabled=True
        )
        user_id = self.master_model.users.add(
            tenant_id=tenant_id,
            username='posiedon',
            email='posie@don.sea',
            password='trident',
            apikey='0v3rThr0wZ3u$',
            enabled=True
        )
        generated_token = instance.add(
            tenant_id=tenant_id,
            user_id=user_id,
        )
        self.assertIsNotNone(generated_token)

        token_data = instance.get_by_username(
            username='posiedon'
        )
        id_token_data = instance.get_by_user_id(
            user_id=user_id
        )
        self.assertEqual(token_data['tenant_id'], tenant_id)
        self.assertEqual(token_data['user_id'], user_id)
        self.assertEqual(token_data['token'], generated_token)
        self.assertEqual(token_data, id_token_data)


class PsuedoDateTime(datetime.datetime):
    pass


@ddt.ddt
class TestKeystoneDbTokenExpiration(TestBase):

    def setUp(self):
        super(TestKeystoneDbTokenExpiration, self).setUp(initialize=False)
        self.model = KeystoneDbTokens
        self.db = self.master_model.database
        from openstackinabox.models.keystone.model import KeystoneModel
        KeystoneModel.initialize_db_schema(self.master_model.database)
        self.master_model.roles.initialize()
        self.master_model.tenants.initialize()
        self.master_model.users.initialize()

        self.dt_old = datetime.datetime
        datetime.datetime = PsuedoDateTime

    def tearDown(self):
        super(TestKeystoneDbTokenExpiration, self).tearDown()
        datetime.datetime = self.dt_old

    @ddt.data(
        (True, False, 'howdy', '2077-01-03 12:55:42'),
        (False, True, '2014-02-24 09:21:18', '2015-05-12 23:09:14'),
        (False, False, '2016-12-15 01:19:56', '2013-11-14 15:12:09')
    )
    @ddt.unpack
    def test_expiration(self, revoked, expired, expire_time, now_time):
        with mock.patch('datetime.datetime.utcnow') as mock_utcnow:
            mock_utcnow.return_value = datetime.datetime.strptime(
                now_time,
                self.model.EXPIRE_TIME_FORMAT
            )

            token_data = {
                'revoked': revoked,
                'expires': expire_time
            }

            if revoked:
                with self.assertRaises(exceptions.KeystoneRevokedTokenError):
                    self.model.check_expiration(token_data)
            elif expired:
                with self.assertRaises(exceptions.KeystoneExpiredTokenError):
                    self.model.check_expiration(token_data)
            else:
                self.model.check_expiration(token_data)

    @ddt.data(
        (False, False, '2014-02-24 09:21:18', '2015-05-12 23:09:14'),
        (False, True, '2016-12-15 01:19:56', '2013-11-14 15:12:09'),
        (True, False, '2014-02-24 09:21:18', '2015-05-12 23:09:14'),
        (True, True, '2016-12-15 01:19:56', '2013-11-14 15:12:09')
    )
    @ddt.unpack
    def test_validate_token(self, revoked, valid_token, expire_time, now_time):
        instance = self.model(
            self.master_model,
            self.db
        )

        tenant_id = self.master_model.tenants.add(
            tenant_name='Neptune',
            description='gods of the sea',
            enabled=True
        )
        user_id = self.master_model.users.add(
            tenant_id=tenant_id,
            username='posiedon',
            email='posie@don.sea',
            password='trident',
            apikey='0v3rThr0wZ3u$',
            enabled=True
        )
        generated_token = (
            instance.add(
                tenant_id=tenant_id,
                user_id=user_id,
                expire_time=datetime.datetime.strptime(
                    expire_time,
                    self.model.EXPIRE_TIME_FORMAT
                )
            )
            if (valid_token or revoked)
            else 'happy-days'
        )
        self.assertIsNotNone(generated_token)

        if revoked:
            instance.revoke(
                tenant_id=tenant_id,
                user_id=user_id,
                token=generated_token
            )

        with mock.patch('datetime.datetime.utcnow') as mock_utcnow:
            mock_utcnow.return_value = datetime.datetime.strptime(
                now_time,
                self.model.EXPIRE_TIME_FORMAT
            )

            if revoked:
                with self.assertRaises(exceptions.KeystoneRevokedTokenError):
                    instance.validate_token(generated_token)
            elif not valid_token:
                with self.assertRaises(exceptions.KeystoneInvalidTokenError):
                    instance.validate_token(generated_token)
            else:
                instance.validate_token(generated_token)
