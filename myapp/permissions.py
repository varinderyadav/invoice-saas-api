from rest_framework.permissions import BasePermission


class IsAuthenticatedUser(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class AdminFullAccessPermission(BasePermission):
    """
    Allows access only to authenticated admin users (is_staff=True).
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class OwnerOrAdminPermission(BasePermission):
    """
    Object-level access:
    - Admins can access any object.
    - Normal users can access only their own objects.
    - DELETE is restricted to admins only.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if request.method == "DELETE":
            return False

        return getattr(obj, "user", None) == request.user
