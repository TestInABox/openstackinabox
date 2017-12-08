"""
OpenStack-In-A-Box Swift Model Exceptions
"""
from openstackinabox.models import base_model


class SwiftExceptions(base_model.BaseModelExceptions):
    """
    Base of the exceptions for the OpenStack-In-A-Box Swift Model
    """


class SwiftUnknownTenantError(SwiftExceptions):
    """
    Unknown Tenant
    """


class SwiftUnknownContainerError(SwiftExceptions):
    """
    Unknown Container Error
    """


class SwiftUnknownObjectError(SwiftExceptions):
    """
    Unknown Object Error
    """
