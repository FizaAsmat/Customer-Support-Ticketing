from rest_framework.permissions import BasePermission
from .models.users import UserType

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserType.CUSTOMER

class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserType.AGENT