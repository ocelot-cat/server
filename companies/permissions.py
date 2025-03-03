from rest_framework.permissions import BasePermission


class IsCompanyMemberOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user == obj.owner or obj.members.filter(id=request.user.id).exists()
        )


class IsCompanyOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner


class IsCompanyAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.role == "admin" and (
            request.user == obj.owner or obj.members.filter(id=request.user.id).exists()
        )
