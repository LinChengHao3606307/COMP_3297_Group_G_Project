from rest_framework import permissions
from .models import *

class DisallowEvery(permissions.BasePermission):
    def has_permission(self, request, view):
        return False


class IsTester(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user) and request.user.is_tester


class IsDeveloper(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user) and request.user.is_developer
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Report):
            if obj.assigned_to:
                return str(request.user) == obj.assigned_to.email
            return True
        return True


class IsProductOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user) and request.user.is_product_owner
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Report):
            return str(request.user) == obj.product.owner.email
        elif isinstance(obj, Product):
            return str(request.user) == obj.owner.email

class IsProjectMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return IsProductOwner().has_permission(request, view) or IsDeveloper().has_permission(request, view)
    
class IsCommentAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Comment):
            return str(request.user) == obj.author.email
        return False
    
class IsUserItself(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            return str(request.user) == obj.email
        return False
    
class CanUpdateReportStatus(permissions.BasePermission):
    # TODO: support more statuses
    def has_object_permission(self, request, view, obj):
        new_status = request.data.get('status')
        if not new_status:
            return True
        new_status = new_status.lower()
        if new_status in ["open", "rejected", "resolved"]:
            return IsProductOwner().has_permission(request, view)
        elif new_status in ["assigned", "fixed"]:
            return IsDeveloper().has_permission(request, view)
        return False
