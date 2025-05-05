from django.core.cache import cache
from django.db.models import (
    F,
    Q,
    Case,
    Count,
    ExpressionWrapper,
    FloatField,
    IntegerField,
    OuterRef,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce, TruncDate
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.metadata import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import ListAPIView, RetrieveAPIView
from products.models import Product, ProductRecord, ProductRecordSnapshot
from .permissions import IsCompanyAdminOrOwner, IsCompanyOwner, IsCompanyMember
from .models import Company, CompanyMembership, Department, Invitation, Notification
from .serializers import (
    CompanySerializer,
    DepartmentSerializer,
    NotificationSerializer,
    CompanyMembershipSerializer,
)
from django.utils import timezone
from datetime import datetime, timedelta
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


class NotificationListView(ListAPIView):
    """
    기능: 특정 회사에 속한 로그인된 사용자의 알림 목록 조회
    허용: 관리자 및 오너
    쿼리 파라미터:
        - is_read: new (읽지 않은 알림)
        - date: today, yesterday, last_7_days, older
        - is_read와 date는 조합 가능
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = CompanyMembersListPagination

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        memberships = CompanyMembership.objects.filter(
            user=self.request.user, role__in=["admin", "owner"]
        )
        if not memberships.exists():
            raise PermissionDenied("관리자 또는 오너인 회사가 없습니다.")

        company_ids = memberships.values_list("company__id", flat=True)
        if company_id not in company_ids:
            raise PermissionDenied("해당 회사에 대한 관리자 또는 오너 권한이 없습니다.")

        queryset = Notification.objects.filter(
            recipient=self.request.user, company_id=company_id
        ).select_related("company", "recipient")

        is_read = self.request.query_params.get("is_read")
        date_filter = self.request.query_params.get("date")

        if date_filter:
            today = timezone.localtime(timezone.now()).date()
            today_start = timezone.make_aware(
                datetime.combine(today, datetime.min.time())
            )
            today_end = timezone.make_aware(
                datetime.combine(today, datetime.max.time())
            )
            yesterday_start = timezone.make_aware(
                datetime.combine(today - timedelta(days=1), datetime.min.time())
            )
            yesterday_end = timezone.make_aware(
                datetime.combine(today - timedelta(days=1), datetime.max.time())
            )
            seven_days_ago = timezone.make_aware(
                datetime.combine(today - timedelta(days=7), datetime.min.time())
            )

            if date_filter == "today":
                queryset = queryset.filter(created_at__range=(today_start, today_end))

            elif date_filter == "yesterday":
                queryset = queryset.filter(
                    created_at__range=(yesterday_start, yesterday_end)
                )

            elif date_filter == "last_7_days":

                start_time = seven_days_ago
                end_time = yesterday_start
                queryset = queryset.filter(created_at__range=(start_time, end_time))

            elif date_filter == "older":

                end_time = seven_days_ago
                queryset = queryset.filter(created_at__lt=end_time)

            else:
                raise ValidationError(
                    {"date": "유효한 값은 today, yesterday, last_7_days, older입니다."}
                )

        if is_read:
            if is_read == "new":
                queryset = queryset.filter(is_read=False)
            else:
                raise ValidationError({"is_read": "유효한 값은 new입니다."})

        return queryset


class NotificationMarkReadView(APIView):
    """
    기능: 알림을 읽음으로 표시
    허용: 해당 회사에 속한 관리자 및 오너
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def patch(self, request, id):
        memberships = CompanyMembership.objects.filter(
            user=self.request.user, role__in=["admin", "owner"]
        )
        if not memberships.exists():
            raise PermissionDenied("관리자 또는 오너인 회사가 없습니다.")
        company_ids = memberships.values_list("company__id", flat=True)

        try:
            notification = Notification.objects.select_related("company").get(
                id=id, recipient=request.user, company__id__in=company_ids
            )
        except Notification.DoesNotExist:
            return Response(
                {"error": "알림을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        notification.is_read = True
        notification.save(update_fields=["is_read"])
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WeeklyProductFlowView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request, company_id):
        cache_key = f"product_flow:company:{company_id}:week:{timezone.now().date().isoformat()}"
        cached_data = cache.get(cache_key)
        if cached_data:
            print(cached_data)
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            company = Company.objects.get(id=company_id)
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            records = (
                ProductRecord.objects.filter(
                    product__company=company,
                    record_date__date__gte=start_of_week,
                    record_date__date__lte=end_of_week,
                )
                .select_related("product")
                .annotate(record_date_trunc=TruncDate("record_date"))
                .values("record_date_trunc", "record_type")
                .annotate(
                    total_pieces=Sum(
                        (F("box_quantity") * Coalesce(F("product__pieces_per_box"), 1))
                        + F("piece_quantity")
                    )
                )
            )

            flow_data = {
                start_of_week + timedelta(days=i): {"in": 0, "out": 0} for i in range(7)
            }
            for record in records:
                date = record["record_date_trunc"]
                total_pieces = record["total_pieces"] or 0
                record_type = record["record_type"]
                if date not in flow_data:
                    continue
                flow_data[date][record_type] = total_pieces

            total_stock = (
                ProductRecordSnapshot.objects.filter(
                    company=company, snapshot_date__lte=today
                )
                .order_by("-snapshot_date")
                .values("snapshot_date")
                .annotate(total_pieces=Sum("total_pieces"))
                .first()
            )
            total_stock = (
                total_stock["total_pieces"]
                if total_stock
                else (
                    ProductRecord.objects.filter(product__company=company).aggregate(
                        total_pieces=Sum(
                            (
                                F("box_quantity")
                                * Coalesce(F("product__pieces_per_box"), 1)
                            )
                            + F("piece_quantity")
                            - F("consumed_quantity"),
                            filter=Q(record_type="in"),
                        )
                    )["total_pieces"]
                    or 0
                )
            )

            response_data = {
                "company_id": company_id,
                "week_start": start_of_week.isoformat(),
                "week_end": end_of_week.isoformat(),
                "total_stock": total_stock,
                "flow_data": [
                    {
                        "date": date.isoformat(),
                        "in": data["in"],
                        "out": data["out"],
                    }
                    for date, data in flow_data.items()
                ],
            }

            cache.set(cache_key, response_data, timeout=3600)
            return Response(response_data, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response(
                {"error": "회사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductListViewPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductListView(APIView):
    """
    ?filter_type=

    - all: 모든 제품 반환 (기본값).
    - shortage: 현재 재고(current_stock)가 100개 미만인 제품.
    - unpopular: 지난 30일 동안 출고 횟수(out_count)가 0인 제품.
    - volatile: 변동률(variation)의 절대값이 10% 초과인 제품
    - interested: 사용자가 관심 등록한 제품 (UserProductInterest 기반)
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = ProductListViewPagination

    @method_decorator(cache_page(60))
    def get(self, request, company_id):
        filter_type = request.query_params.get("filter_type", "all")
        only_interested = filter_type == "interested"
        page = request.query_params.get("page", "1")
        cache_key = (
            f"products:company:{company_id}:filter_type:{filter_type}:page:{page}"
        )
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            company = Company.objects.get(id=company_id)
            today = timezone.now().date()
            last_month = today - timedelta(days=30)

            out_count_subquery = (
                ProductRecord.objects.filter(
                    product=OuterRef("pk"),
                    record_type="out",
                    record_date__gte=last_month,
                )
                .values("product")
                .annotate(count=Count("id"))
                .values("count")[:1]
            )

            products = Product.objects.filter(company=company).annotate(
                out_count=Coalesce(Subquery(out_count_subquery), 0),
                is_volatile=Case(
                    When(
                        Q(variation__gt=10) | Q(variation__lt=-10),
                        then=Value(1, output_field=IntegerField()),
                    ),
                    default=Value(0, output_field=IntegerField()),
                    output_field=IntegerField(),
                ),
            )

            if only_interested:
                products = products.filter(userproductinterest__user=request.user)
            elif filter_type == "shortage":
                products = products.filter(current_stock__lt=100)
            elif filter_type == "unpopular":
                products = products.filter(out_count=0)
            elif filter_type == "volatile":
                products = products.filter(is_volatile=1)
            elif filter_type != "all":
                raise ValidationError({"filter_type": "유효하지 않은 필터 타입입니다."})

            products = products.select_related("company")

            # Pagination
            paginator = self.pagination_class()
            paginated_products = paginator.paginate_queryset(products, request)
            response_data = [
                {
                    "id": product.id,
                    "name": product.name,
                    "unit": product.unit,
                    "stock": product.current_stock,
                    "variation": round(product.variation, 2),
                    "out_count": product.out_count,
                }
                for product in paginated_products
            ]

            cache.set(cache_key, response_data, timeout=60)
            return paginator.get_paginated_response(response_data)
        except Company.DoesNotExist:
            return Response(
                {"error": "회사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
