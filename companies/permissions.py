from rest_framework.permissions import BasePermission
from companies.models import CompanyMembership


class IsCompanyMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            obj.members.filter(id=request.user.id).exists() or request.user == obj.owner
        )


class IsCompanyOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner


class IsCompanyAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        membership = CompanyMembership.objects.get(company=obj, user=request.user)
        return membership and (membership.role == "owner" or membership.role == "admin")
