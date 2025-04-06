from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import (
    IsCompanyAdminOrOwner,
    IsCompanyOwner,
)
from .models import Company, CompanyMembership, Department, Invitation, Notification
from .serializers import CompanySerializer, DepartmentSerializer, NotificationSerializer
from django.utils import timezone
from datetime import timedelta
import uuid


class CompanyView(APIView):
    """
    기능 : 회사를 만들 수 있습니다.
    허용 : 누구나
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = Company.objects.filter(
            Q(members=request.user) | Q(owner=request.user)
        ).distinct()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save(owner=request.user)
            CompanyMembership.objects.create(
                company=company, user=request.user, role="owner"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyDetailView(APIView):
    """
    기능 : 회사의 상세 정보를 조회/수정/삭제합니다.
    허용 : 회사 오너만
    """

    permission_classes = [IsAuthenticated, IsCompanyOwner]

    def get_object(self, pk):
        try:
            obj = Company.objects.get(pk=pk)
            self.check_object_permissions(self.request, obj)
            return obj
        except Company.DoesNotExist:
            return None

    def get(self, request, pk):
        company = self.get_object(pk)
        if not company:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company)
        return Response(serializer.data)

    def put(self, request, pk):
        company = self.get_object(pk)
        if not company:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = CompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        company = self.get_object(pk)
        if not company:
            return Response(status=status.HTTP_404_NOT_FOUND)

        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyMembersListView(APIView):
    """
    기능 : 회사 멤버를 볼 수 있습니다.
    허용 : 관리자와 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyAdminOrOwner]

    def get(self, request, company_id):
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "회사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, company)

        memberships = CompanyMembership.objects.filter(company=company).select_related(
            "user", "department"
        )

        data = [
            {
                "user": membership.user.username,
                "role": membership.role,
                "department": (
                    membership.department.name if membership.department else "미지정"
                ),
            }
            for membership in memberships
        ]

        return Response(data)


class CompanyPromoteMembersView(APIView):
    """
    기능 : 회사 멤버를 승격시킬 수 있습니다.
    허용 : 관리자와 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyAdminOrOwner]

    def patch(self, request, company_id, user_id):
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "회사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, company)

        try:
            membership = CompanyMembership.objects.get(company=company, user_id=user_id)
        except CompanyMembership.DoesNotExist:
            return Response(
                {"error": "사용자가 회사의 멤버가 아닙니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if membership.role == "admin":
            return Response(
                {"error": "이미 관리자입니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        membership.role = "admin"
        membership.save()

        return Response(
            {"message": f"{membership.user.username}님이 관리자로 승격되었습니다."},
            status=status.HTTP_200_OK,
        )


class DepartmentView(APIView):
    """
    기능 : 부서를 만들 수 있습니다.
    허용 : 회사 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyOwner]

    def post(self, request, company_id):
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "회사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, company)

        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(company=company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentDetailView(APIView):
    """
    기능 : 부서의 상세 정보를 조회/수정/삭제합니다.
    허용 : 회사 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyOwner]

    def get_object(self, pk):
        try:
            obj = Department.objects.get(pk=pk)
            self.check_object_permissions(self.request, obj.company)
            return obj
        except Department.DoesNotExist:
            return None

    def get(self, request, pk):
        department = self.get_object(pk)
        if not department:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DepartmentSerializer(department)
        return Response(serializer.data)

    def put(self, request, pk):
        department = self.get_object(pk)
        if not department:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DepartmentSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        department = self.get_object(pk)
        if not department:
            return Response(status=status.HTTP_404_NOT_FOUND)
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationCreateView(APIView):
    """
    기능 : 초대 링크를 생성할 수 있습니다.
    허용 : 회사 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyOwner]

    def post(self, request, company_id):
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "회사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, company)

        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "이메일을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        token = str(uuid.uuid4())
        expiration_date = timezone.now() + timedelta(days=7)
        invitation = Invitation.objects.create(
            company=company,
            email=email,
            token=token,
            expiration_date=expiration_date,
        )

        # 이메일 발송 로직

        return Response({"message": "초대가 생성되었습니다.", "token": token})


class InvitationAcceptView(APIView):
    """
    기능 : 초대받은 링크를 수락할 수 있습니다.
    허용 : 누구나
    """

    def get(self, request, token):
        try:
            invitation = Invitation.objects.get(
                token=token,
                expiration_date__gt=timezone.now(),
                is_used=False,
            )
        except Invitation.DoesNotExist:
            return Response(
                {"error": "유효하지 않거나 만료된 초대입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user if request.user.is_authenticated else None
        if not user:
            return Response({"redirect": "/signup/?invitation_token=" + token})

        CompanyMembership.objects.create(company=invitation.company, user=user)

        invitation.is_used = True
        invitation.is_accepted = True
        invitation.save()

        return Response({"message": "초대가 수락되었습니다."})


class NotificationListView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdminOrOwner]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            company__in=self.request.user.companies.filter(
                companymembership__role__in=["admin", "owner"]
            ),
        ).select_related("company", "recipient")
