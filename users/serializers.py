from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from companies.serializers import CompanyMembershipSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    company_memberships = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "pk",
            "username",
            "email",
            "company_memberships",
        ]

    def get_company_memberships(self, obj):
        membership = obj.company_membership
        if membership:
            return CompanyMembershipSerializer(membership).data
        return None


class TokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["pk"] = user.pk
        return token
