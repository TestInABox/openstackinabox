"""
OpenStack Keystone v2 Service Mock Exceptions
"""
from openstackinabox.models.keystone.exceptions import *  # noqa: F403,F401


class KeystoneV2Errors(Exception):
    pass


class KeystoneV2AuthError(Exception):
    pass


class KeystoneV2AuthForbiddenError(KeystoneV2AuthError):
    pass


class KeystoneV2AuthUnauthorizedError(KeystoneV2AuthError):
    pass
