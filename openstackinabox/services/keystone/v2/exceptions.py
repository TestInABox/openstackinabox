"""
OpenStack Keystone v2 Service Mock Exceptions
"""


class KeystoneV2Errors(Exception):
    pass


class KeystoneV2AuthError(Exception):
    pass


class KeystoneV2AuthForbiddenError(KeystoneV2AuthError):
    pass


class KeystoneV2AuthUnauthorizedError(KeystoneV2AuthError):
    pass
