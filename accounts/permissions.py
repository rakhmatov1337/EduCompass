from rest_framework import permissions

class IsEduCenterOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'EDU_CENTER'
        )
    
class IsBranchOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'BRANCH'
        )

class IsEduCenter(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'EDU_CENTER'
        )
    
class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'SUPERUSER'
        )


class IsEduCenterOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'EDU_CENTER'
        )
