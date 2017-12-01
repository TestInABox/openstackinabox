.. _faq:

Frequently Asked Questions
==========================

Why not use Mimic_?
-------------------

Mimic is a great tool for what it does. However, it still introduces external
dependencies and potential errors that have nothing to do with your testing as
it is a server that runs outside your testing framework over the network -
locally or otherwise.

Local, unit testing should use a tool like StackInABox; while more formal
integration testing where multiple systems may be interacting together and all
need to have a common mocked backend fit better with Mimic_; though work is
underway to create a means of using existing Stack-In-A-Box services to
provide a similar role as Mimic_ via StackInAWSGI_.

References
----------

.. _Mimic: https://pypi.python.org/pypi/mimic/
.. _StackInAWSGI: https://github.com/TestInABox/stackInAWSGI
