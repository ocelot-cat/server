from rest_framework.metadata import PermissionDenied
from rest_framework.permissions import BasePermission
from companies.models import Company, CompanyMembership


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
        if isinstance(obj, Company):
            company = obj
        elif isinstance(obj, CompanyMembership):
            company = obj.company
        else:
            raise PermissionDenied("유효하지 않은 객체입니다.")

        membership = CompanyMembership.objects.filter(
            company=company, user=request.user
        ).first()
        return membership and (membership.role == "owner" or membership.role == "admin")
