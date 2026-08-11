from rest_framework import serializers

from books.serializers import BookDetailSerializer
from borrowings.models import Borrowing


class BorrowingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a borrowing."""

    class Meta:
        model = Borrowing
        fields = ("id", "expected_return_date", "book")

    def validate_book(self, value):
        if value.inventory <= 0:
            raise serializers.ValidationError(
                "This book is out of stock."
            )
        return value


class BorrowingReturnSerializer(serializers.ModelSerializer):
    """Serializer for returning a borrowing."""

    class Meta:
        model = Borrowing
        fields = ("id",)
        read_only_fields = ("id",)

    def validate(self, attrs):
        if self.instance.actual_return_date is not None:
            raise serializers.ValidationError(
                "This borrowing has already been returned."
            )
        return attrs


class BorrowingListSerializer(serializers.ModelSerializer):
    """Serializer for listing borrowings (summary view)."""

    book_title = serializers.CharField(source="book.title", read_only=True)
    book_author = serializers.CharField(source="book.author", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book_title",
            "book_author",
        )


class BorrowingDetailSerializer(serializers.ModelSerializer):
    """Serializer for borrowing detail with nested book info."""

    book = BookDetailSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
