from rest_framework import serializers
from .models import Company, CompanyMembership, Department, Notification


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "owner"]


class CompanyMembershipSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(source="company.id")
    company_name = serializers.CharField(source="company.name")
    role = serializers.CharField(source="get_role_display")  # 한글 역할 표시

    class Meta:
        model = CompanyMembership
        fields = ["company_id", "company_name", "role"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "target_url", "is_read", "created_at"]
