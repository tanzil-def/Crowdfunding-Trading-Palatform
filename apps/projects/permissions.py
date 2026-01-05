from rest_framework import permissions

# ------------------ Developer Ownership ------------------
class IsDeveloperOwner(permissions.BasePermission):
    """
    Allow access only if request.user is the project's developer.
    """
    def has_object_permission(self, request, view, obj):
        return obj.developer == request.user and request.user.is_developer


# ------------------ Project Editable ------------------
class IsProjectEditable(permissions.BasePermission):
    """
    Allow edit only if project status is DRAFT or NEEDS_CHANGES.
    SAFE_METHODS (GET, HEAD, OPTIONS) always allowed.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.status in ['DRAFT', 'NEEDS_CHANGES']


# ------------------ Submit Project ------------------
class CanSubmitProject(permissions.BasePermission):
    """
    Only allow submission if project status is DRAFT.
    """
    def has_object_permission(self, request, view, obj):
        return obj.status == 'DRAFT'


# ------------------ Archive Project ------------------
class CanArchiveProject(permissions.BasePermission):
    """
    Allow archive only if project is NOT in PENDING_REVIEW or APPROVED.
    """
    def has_object_permission(self, request, view, obj):
        return obj.status not in ['PENDING_REVIEW', 'APPROVED']


# ------------------ Manage Project Media ------------------
class CanManageProjectMedia(permissions.BasePermission):
    """
    Allow managing media only if request.user is the project's developer.
    Works for Project or ProjectMedia object.
    """
    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, 'developer') else obj.project
        return project.developer == request.user
