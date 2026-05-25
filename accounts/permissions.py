from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        allowed_roles = getattr(view, 'allowed_roles', self.allowed_roles)
        return not allowed_roles or request.user.role in allowed_roles or request.user.is_superuser


class IsAdminOrManager(RolePermission):
    allowed_roles = ('admin', 'manager')


class IsAdmin(RolePermission):
    allowed_roles = ('admin',)


class IsSalesStaff(RolePermission):
    allowed_roles = ('admin', 'manager', 'cashier')


class IsInventoryStaff(RolePermission):
    allowed_roles = ('admin', 'manager', 'storekeeper')


class IsReportsStaff(RolePermission):
    allowed_roles = ('admin', 'manager')
