from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    """Base serializer for creating/updating books."""

    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")


class BookListSerializer(BookSerializer):
    """Serializer for listing books (summary view)."""

    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory")


class BookDetailSerializer(BookSerializer):
    """Serializer for book detail with all fields."""

    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")
