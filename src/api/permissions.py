from rest_framework import permissions


class IsDeveloper(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user) and hasattr(request.user, "developer")
    
    def has_object_permission(self, request, view, obj):
        return str(request.user) == obj.assigned_to.username


class IsProductOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user) and hasattr(request.user, "productowner")
    
    def has_object_permission(self, request, view, obj):
        return str(request.user) == obj.product.owner.username


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
