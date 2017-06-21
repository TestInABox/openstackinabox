"""
Keystone Model Exceptions
"""
from openstackinabox.models.base_model import BaseModelExceptions


class KeystoneError(BaseModelExceptions):
    pass


class KeystoneTenantError(KeystoneError):
    pass


class KeystoneUserError(KeystoneError):
    pass


class KeystoneDisabledUserError(KeystoneUserError):
    pass


class KeystoneUnknownUserError(KeystoneUserError):
    pass


class KeystoneUserAuthError(KeystoneUserError):
    pass


class KeystoneUserInvalidPasswordError(KeystoneUserAuthError):
    pass


class KeystoneUserInvalidApiKeyError(KeystoneUserAuthError):
    pass


class KeystoneTokenError(KeystoneError):
    pass


class KeystoneInvalidTokenError(KeystoneTokenError):
    pass


class KeystoneRevokedTokenError(KeystoneInvalidTokenError):
    pass


class KeystoneExpiredTokenError(KeystoneInvalidTokenError):
    pass


class KeystoneRoleError(KeystoneError):
    pass


class KeystoneServiceCatalogError(KeystoneError):
    pass


class KeystoneServiceCatalogServiceError(KeystoneServiceCatalogError):
    pass


class KeystoneServiceCatalogEndpointError(KeystoneServiceCatalogError):
    pass


class KeystoneEndpointUrlError(KeystoneServiceCatalogEndpointError):
    pass
