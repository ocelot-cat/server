from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Activity
from .serializers import ActivitySerializer
from django.core.paginator import Paginator


class UserActivityListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page_number = request.GET.get("page", 1)
        activities = (
            Activity.objects.filter(recipient=request.user)
            .select_related("actor", "post")
            .order_by("-created_at")
        )

        paginator = Paginator(activities, 20)
        page_obj = paginator.get_page(page_number)

        serializer = ActivitySerializer(page_obj, many=True)
        return Response(
            {
                "activities": serializer.data,
                "has_next": page_obj.has_next(),
                "total_pages": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )
