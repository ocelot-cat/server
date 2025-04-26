from rest_framework import serializers
from .models import Company, CompanyMembership, Department, Notification


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "owner"]


class CompanyMembershipSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(source="company.id")
    company_name = serializers.CharField(source="company.name")
    role = serializers.CharField(source="get_role_display")
    username = serializers.CharField(source="user.username")
    email = serializers.EmailField(source="user.email")
    department = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source="user.id")

    class Meta:
        model = CompanyMembership
        fields = [
            "user_id",
            "company_id",
            "company_name",
            "role",
            "username",
            "email",
            "department",
        ]

    def get_department(self, obj):
        return obj.department.name if obj.department else "미지정"


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "target_url", "is_read", "created_at"]
