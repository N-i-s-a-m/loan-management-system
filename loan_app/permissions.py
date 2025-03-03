# File: permissions.py
# Description: Custom permission classes for controlling access based on user roles.

from rest_framework.permissions import BasePermission


# Permission class for admin users
class IsAdminUser(BasePermission):
    """
    Allows access only to authenticated users with the 'admin' role.
    """
    def has_permission(self, request, view):
        # Check if user is authenticated and has 'admin' role
        return request.user.is_authenticated and request.user.role == 'admin'


# Permission class for normal users
class IsUser(BasePermission):
    """
    Allows access only to authenticated users with the 'user' role.
    """
    def has_permission(self, request, view):
        # Check if user is authenticated and has 'user' role
        return request.user.is_authenticated and request.user.role == 'user'