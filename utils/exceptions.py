from rest_framework.exceptions import APIException
from rest_framework import status


class UnverifiedUserError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'User email is not verified.'
    default_code = 'unverified_user'


class ResourceConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A conflict occurred with the current state of the resource.'
    default_code = 'resource_conflict'


class AuthenticationFailedError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Incorrect authentication credentials.'
    default_code = 'authentication_failed'


class PermissionDeniedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'


class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The requested resource was not found.'
    default_code = 'not_found'
