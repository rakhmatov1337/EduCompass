from rest_framework import permissions


class IsSuperUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsEduCenterOrBranch(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ['EDU_CENTER', 'BRANCH']


class IsEduCenterBranchOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # POST/PUT/PATCH/DELETE
        return bool(
            request.user.is_authenticated and
            request.user.role in ['EDU_CENTER', 'BRANCH']
        )
