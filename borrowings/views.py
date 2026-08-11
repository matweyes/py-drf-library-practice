from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingCreateSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingReturnSerializer,
)


@extend_schema(tags=["Borrowings"])
@extend_schema_view(
    list=extend_schema(
        description="List borrowings. Non-admin users see only their own.",
        parameters=[
            OpenApiParameter(
                name="is_active",
                description="Filter by active (not returned) borrowings.",
                type=bool,
            ),
            OpenApiParameter(
                name="user_id",
                description="Filter by user ID (admin only).",
                type=int,
            ),
            OpenApiParameter(
                name="is_overdue",
                description="Filter by overdue borrowings (admin only).",
                type=bool,
            ),
        ],
    ),
    retrieve=extend_schema(description="Retrieve detailed info about a specific borrowing."),
    create=extend_schema(description="Create a new borrowing. Book inventory is decremented by 1."),
)
class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        else:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            is_active = is_active.lower() in ("true", "1")
            if is_active:
                queryset = queryset.filter(actual_return_date__isnull=True)
            else:
                queryset = queryset.filter(actual_return_date__isnull=False)

        if self.request.user.is_staff:
            is_overdue = self.request.query_params.get("is_overdue")
            if is_overdue is not None and is_overdue.lower() in ("true", "1"):
                queryset = queryset.filter(
                    expected_return_date__lt=timezone.now().date(),
                    actual_return_date__isnull=True,
                )

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "return_borrowing":
            return BorrowingReturnSerializer
        return BorrowingListSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            borrowing = serializer.save(user=self.request.user)
            book = borrowing.book
            book.inventory -= 1
            book.save(update_fields=["inventory"])

    @extend_schema(
        description="Return a borrowing. Sets actual_return_date and increments book inventory.",
    )
    @action(detail=True, methods=["post"], url_path="return")
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing, data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            borrowing.actual_return_date = timezone.now().date()
            borrowing.save(update_fields=["actual_return_date"])
            book = borrowing.book
            book.inventory += 1
            book.save(update_fields=["inventory"])

        return Response(
            BorrowingDetailSerializer(borrowing).data,
            status=status.HTTP_200_OK,
        )
