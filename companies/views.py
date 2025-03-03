from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from users.serializers import UserSerializer
from .permissions import IsCompanyMemberOrOwner, IsCompanyOwner, IsCompanyAdmin
from .models import Company, Invitation
from .serializers import CompanySerializer
from django.utils import timezone
from datetime import timedelta
import uuid


class CompanyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = Company.objects.filter(
            Q(members=request.user) | Q(owner=request.user)
        ).distinct()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != "owner":
            raise PermissionDenied("회사를 생성할 권한이 없습니다.")
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMemberOrOwner]

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
        if not IsCompanyOwner().has_object_permission(
            request, self, company
        ) and not IsCompanyAdmin().has_object_permission(request, self, company):
            raise PermissionDenied("회사 정보를 수정할 권한이 없습니다.")
        serializer = CompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        company = self.get_object(pk)
        if not company:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not IsCompanyOwner().has_object_permission(request, self, company):
            raise PermissionDenied("회사를 삭제할 권한이 없습니다.")
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyMembersListView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMemberOrOwner]

    def get(self, request, company_id):
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "회사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, company)

        members = company.members.all()
        serializer = UserSerializer(members, many=True)
        return Response(serializer.data)


class InvitationCreateView(APIView):
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
            company=company, email=email, token=token, expiration_date=expiration_date
        )

        # 이메일 발송 로직

        return Response({"message": "초대가 생성되었습니다.", "token": token})


class InvitationAcceptView(APIView):
    def get(self, request, token):
        try:
            invitation = Invitation.objects.get(
                token=token, expiration_date__gt=timezone.now(), is_used=False
            )
        except Invitation.DoesNotExist:
            return Response(
                {"error": "유효하지 않거나 만료된 초대입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user if request.user.is_authenticated else None
        if not user:
            return Response({"redirect": "/signup/?invitation_token=" + token})

        invitation.company.members.add(user)
        invitation.is_used = True
        invitation.is_accepted = True
        invitation.save()

        return Response({"message": "초대가 수락되었습니다."})
