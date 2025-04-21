from rest_framework.permissions import BasePermission


class IsOwnUser(BasePermission):
    def has_permission(self, request, view):
        pk = view.kwargs.get("pk")
        return request.user.is_authenticated and str(request.user.pk) == str(pk)
