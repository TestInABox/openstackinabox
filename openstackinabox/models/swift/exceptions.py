"""
"""


class SwiftExceptions(Exception):
    pass


class SwiftUnknownTenantError(SwiftExceptions):
    pass


class SwiftUnknownContainerError(SwiftExceptions):
    pass


class SwiftUnknownObjectError(SwiftExceptions):
    pass
