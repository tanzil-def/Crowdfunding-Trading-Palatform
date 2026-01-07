<<<<<<< HEAD
=======
from rest_framework.permissions import BasePermission

class IsDeveloper(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'DEVELOPER'


class IsProjectOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.developer == request.user


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'


class CanViewMedia(BasePermission):
    def has_object_permission(self, request, view, obj):

        if not obj.is_restricted:
            return True

        if not request.user.is_authenticated:
            return False

        if request.user.role == 'ADMIN':
            return True

        if request.user == obj.project.developer:
            return True

        return False
>>>>>>> 83d38a9 (WIP: work in progress on project features)
