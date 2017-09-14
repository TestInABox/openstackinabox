First Step
----------

Before continuing be sure to :ref:`install <install>` OpenStackInABox
in your test environment. Any supported OpenStack Service will now
be available to the tests with a few simple steps.

To start, the tests must be orchestrated with StackInABox:

.. code-block:: python

    import unittest

    import requests

    import stackinabox.util.requests_mock

    class TestRequestsMock(unittest.TestCase):

        def setUp(self):
            super(TestRequestsMock, self).setUp()
            self.session = requests.Session()

        def tearDown(self):
            super(TestRequestsMock, self).tearDown()
            StackInABox.reset_services()
            self.session.close()

        def test_basic_requests_mock(self):
            with stackinabox.util.requests_mock.core.activate():
                stackinabox.util.requests_mock.core.requests_mock_registration(
                    'localhost'
                )

After StackInABox is configured, then the desired services can be added:

.. code-block:: python

    import unittest

    import requests

    import stackinabox.util.requests_mock

    # Import OpenStack Keystone Service
    from openstackinabox.services.keystone import KeystoneV2Service

    class TestRequestsMock(unittest.TestCase):

        def setUp(self):
            super(TestRequestsMock, self).setUp()
            # Create an instance of the service
            self.keystone = KeystoneV2Service()
            # Register the service into StackInABox
            StackInABox.register_service(self.keystone)
            self.session = requests.Session()

        def tearDown(self):
            super(TestRequestsMock, self).tearDown()
            StackInABox.reset_services()
            self.session.close()

        def test_basic_requests_mock(self):
            with stackinabox.util.requests_mock.core.activate():
                stackinabox.util.requests_mock.core.requests_mock_registration(
                    'localhost'
                )

                # Keystone URL: http://localhost/keystone/v2.0/
                # Now you can use the Keystone Service


.. note:: Depending on what the test is doing it may be necessary to add data
    into the Service Model. If there are inter-model dependencies then all
    the involved models will need to have the data added.
