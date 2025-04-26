from django.db.models import Q
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .permissions import IsCompanyAdminOrOwner, IsCompanyOwner, IsCompanyMember
from .models import Company, CompanyMembership, Department, Invitation, Notification
from .serializers import (
    CompanySerializer,
    DepartmentSerializer,
    NotificationSerializer,
    CompanyMembershipSerializer,
)
from django.utils import timezone
from datetime import timedelta
import uuid
from rest_framework import serializers


class CompanyMembersListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CompanyViewSet(ModelViewSet):
    """
    기능: 회사 생성, 조회, 수정, 삭제
    허용:
        - 생성: 인증된 사용자
        - 조회, 수정, 삭제: 관리자 및 오너
    """

    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_queryset(self):
        queryset = Company.objects.select_related("owner").prefetch_related("members")
        if self.action == "list":
            memberships = CompanyMembership.objects.filter(
                user=self.request.user, role__in=["admin", "owner"]
            ).values_list("company__id", flat=True)
            queryset = queryset.filter(id__in=memberships)
        return queryset

    def perform_create(self, serializer):
        company = serializer.save(owner=self.request.user)
        CompanyMembership.objects.create(
            company=company, user=self.request.user, role="owner"
        )

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsCompanyAdminOrOwner()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyMembersListView(ListAPIView):
    """
    기능: 회사 멤버 목록 조회 (부서 필터링 가능)
    허용: 관리자 및 오너
    쿼리 파라미터:
        - sort: latest, oldest, name (기본: latest)
        - department_id: 부서 ID로 필터링
        - department_name: 부서 이름으로 필터링
        - page: 페이지 번호
    """

    permission_classes = [IsAuthenticated, IsCompanyAdminOrOwner]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = CompanyMembersListPagination
    serializer_class = CompanyMembershipSerializer

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            raise NotFound({"error": "회사를 찾을 수 없습니다."})

        self.check_object_permissions(self.request, company)

        sort = self.request.query_params.get("sort", "latest")
        department_id = self.request.query_params.get("department_id")
        department_name = self.request.query_params.get("department_name")

        memberships = CompanyMembership.objects.filter(company=company).select_related(
            "user", "department"
        )

        if department_id:
            try:
                memberships = memberships.filter(department__id=int(department_id))
            except ValueError:
                raise serializers.ValidationError({"department_id": "숫자여야 합니다."})
            if not memberships.exists():
                raise NotFound(
                    {"error": "해당 부서에 멤버가 없거나 부서가 존재하지 않습니다."}
                )
        elif department_name:
            if department_name == "":
                memberships = memberships.filter(department__isnull=True)
            else:
                memberships = memberships.filter(department__name=department_name)
            if not memberships.exists():
                raise NotFound(
                    {"error": "해당 부서에 멤버가 없거나 부서가 존재하지 않습니다."}
                )

        if sort == "latest":
            memberships = memberships.order_by("-created_at")
        elif sort == "oldest":
            memberships = memberships.order_by("created_at")
        elif sort == "name":
            memberships = memberships.order_by("user__username")
        else:
            raise serializers.ValidationError(
                {"sort": "잘못된 정렬 기준입니다. (latest, oldest, name 중 선택)"}
            )

        return memberships


class CompanyMemberDetailView(RetrieveAPIView):
    """
    기능: 특정 회사 멤버의 상세 정보 조회
    허용: 관리자 및 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyAdminOrOwner]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    serializer_class = CompanyMembershipSerializer

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            raise NotFound({"error": "회사를 찾을 수 없습니다."})

        return CompanyMembership.objects.filter(company=company).select_related(
            "user", "department"
        )

    def get_object(self):
        queryset = self.get_queryset()
        user_id = self.kwargs["user_id"]
        try:
            membership = queryset.get(user_id=user_id)
        except CompanyMembership.DoesNotExist:
            raise NotFound({"error": "사용자가 회사의 멤버가 아닙니다."})
        return membership


class CompanyPromoteMembersView(APIView):
    """
    기능: 회사 멤버를 관리자로 승격
    허용: 관리자 및 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyAdminOrOwner]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

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


class DepartmentViewSet(ModelViewSet):
    """
    기능: 부서 생성, 조회, 수정, 삭제
    허용: 오너
    """

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsCompanyOwner]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_queryset(self):
        company_id = self.request.query_params.get("company_id") or self.kwargs.get(
            "company_id"
        )
        if not company_id:
            raise ValidationError({"company_id": "회사 ID가 필요합니다."})
        return Department.objects.filter(company_id=company_id).select_related(
            "company"
        )

    def perform_create(self, serializer):
        company_id = self.request.data.get("company_id") or self.kwargs.get(
            "company_id"
        )
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            raise NotFound({"error": "회사를 찾을 수 없습니다."})
        self.check_object_permissions(self.request, company)
        serializer.save(company=company)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance.company)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance.company)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance.company)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationCreateView(APIView):
    """
    기능: 초대 링크 생성
    허용: 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyOwner]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

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

        return Response({"message": "초대가 생성되었습니다.", "token": token})


class InvitationAcceptView(APIView):
    """
    기능: 초대 링크 수락
    허용: 누구나
    """

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "토큰이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST
            )

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
            return Response(
                {"error": "인증이 필요합니다. 회원가입 후 초대를 수락해주세요."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        CompanyMembership.objects.create(company=invitation.company, user=user)

        invitation.is_used = True
        invitation.is_accepted = True
        invitation.save()

        return Response({"message": "초대가 수락되었습니다."})


class NotificationListView(APIView):
    """
    기능: 특정 회사에 속한 모든 알림 목록 조회
    허용: 관리자 및 오너
    """

    permission_classes = [IsAuthenticated, IsCompanyAdminOrOwner]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request, company_id):
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "회사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, company)

        notifications = (
            Notification.objects.filter(company=company)
            .select_related("company", "recipient")
            .order_by("-created_at")
        )
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    """
    기능: 알림을 읽음으로 표시
    허용: 인증된 사용자
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def patch(self, request, id):
        try:
            notification = Notification.objects.get(id=id, recipient=request.user)
        except Notification.DoesNotExist:
            return Response(
                {"error": "알림을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        notification.is_read = True
        notification.save(update_fields=["is_read"])
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
