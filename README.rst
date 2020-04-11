******************
OpenStack-In-A-Box
******************

Stack-In-A-Box-based OpenStack Services for use with Testing Framesworks


.. image:: https://travis-ci.org/TestInABox/openstackinabox.svg?branch=master
   :target: https://travis-ci.org/TestInABox/openstackinabox
   :alt: Travis-CI Status


.. image:: https://coveralls.io/repos/TestInABox/openstackinabox/badge.svg
  :target: https://coveralls.io/r/TestInABox/openstackinabox
  :alt: Coverage Status

.. image:: https://badges.gitter.im/TestInABox/community.svg
  :target: https://gitter.im/TestInABox/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge
  :alt: Gitter

========
Overview
========

``Stack-In-A-Box`` provides the ability to use mocked RESTful APIs naturally inside unit tests by using modules such as ``HTTPretty`` or ``Requests-Mock``. ``OpenStack-In-A-Box`` provides a series of mocked OpenStack Services inside the ``Stack-In-A-Box`` framework, thus providing a reliable mock-up of the OpenStack Services that can be utilized by applications written against them.

==========
Installing
==========

Installation is simple:

.. code-block:: bash

	pip install openstackinabox

=====
Goals
=====

- Enable Python modules to be unit tested against OpenStack services in an environment controlled by the unit tests.
- Provide reliable, accurate mock-ups of the services
- Enable unit testing to not have to mock the various tools, e.g KeystoneClient API, to perform their tests.
- Support both Positive and Negative testing
- Testing should be easy to do:

	- you should not necessarily need to know the ins and outs of each service
	- you should be able to register what you need (f.e authenticaiton, storage) and have it just work

- should be usable on systems like Travis (https://travis-ci.org/)
- should be light on requirements

	- we do not want to bloat your testing to fit our needs
	- if we have many requirements they could interfere with your requirements

- The code being unit-tested should not be able to tell the difference of whether it is working with ``OpenStack-In-A-Box`` or the real thing

	- there should be nothing special about setting up the test
	- if you don't turn on OpenStack-In-A-Box (and ``Stack-In-A-Box`` upon which it is built) then the code should be able to call the real thing
	- caveat: the utility tools (f.e httpretty, requests-mock) will determine the URL for the services being provided; see ``Stack-In-A-Box`` for details.

=========================
Why not use framekwork X?
=========================

This is a natural extension of ``Stack-In-A-Box`` to provide OpenStack services to the unit testing being done. If you are using ``Stack-In-A-Box`` then it makes sense to also use ``OpenStack-In-A-Box`` as it is simply providing a compatible set of OpenStack services that simply need to be registered with ``Stack-In-A-Box``.

================
What's Provided?
================

Current work is on supporting the OpenStack Keystone v2 services. See the Issues and Milestone for more details.

=======================
Working with Frameworks
=======================

``OpenStack-In-A-Box`` builds on ``Stack-In-A-Box``. Simply instantiate the desired service and register it with ``Stack-In-A-Box``.

==========
References
==========

- ``Stack-In-A-Box`` - https://github.com/TestInABox/stackInABox/
- ``OpenStack`` - https://www.openstack.org/
- ``OpenStack Keystone`` - http://docs.openstack.org/developer/keystone/
