"""
Keystone Model Exceptions
"""
from openstackinabox.models.base_model import BaseModelExceptions


class KeystoneError(BaseModelExceptions):
    """
    Base Keystone Model Exception
    """


class KeystoneTenantError(KeystoneError):
    """
    Tenant Related Errors
    """


class KeystoneUserError(KeystoneError):
    """
    User Related Errors
    """


class KeystoneDisabledUserError(KeystoneUserError):
    """
    User is disabled
    """


class KeystoneUnknownUserError(KeystoneUserError):
    """
    Unknown User Error
    """


class KeystoneUserAuthError(KeystoneUserError):
    """
    User Authentication Error
    """


class KeystoneUserInvalidPasswordError(KeystoneUserAuthError):
    """
    User Password is invalid
    """


class KeystoneUserInvalidApiKeyError(KeystoneUserAuthError):
    """
    User API Key is invalid
    """


class KeystoneTokenError(KeystoneError):
    """
    Token related errors
    """


class KeystoneInvalidTokenError(KeystoneTokenError):
    """
    Invalid Token Error
    """


class KeystoneRevokedTokenError(KeystoneInvalidTokenError):
    """
    Token Invalid due to being explicitly revoked
    """


class KeystoneExpiredTokenError(KeystoneInvalidTokenError):
    """
    Token invalid due to expiration
    """


class KeystoneRoleError(KeystoneError):
    """
    Role related errors
    """


class KeystoneServiceCatalogError(KeystoneError):
    """
    Service Catalog related errors
    """


class KeystoneServiceCatalogServiceError(KeystoneServiceCatalogError):
    """
    Service Catalog Service entry error
    """


class KeystoneServiceCatalogEndpointError(KeystoneServiceCatalogError):
    """
    Service Catalog Endpoint Error
    """


class KeystoneEndpointUrlError(KeystoneServiceCatalogEndpointError):
    """
    Service Catalog Endpoint URL Error
    """
