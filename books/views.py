from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from books.models import Book
from books.serializers import (
    BookSerializer,
    BookListSerializer,
    BookDetailSerializer,
)


@extend_schema(tags=["Books"])
@extend_schema_view(
    list=extend_schema(description="List all books in the library."),
    retrieve=extend_schema(description="Retrieve detailed info about a specific book."),
    create=extend_schema(description="Add a new book to the library."),
    update=extend_schema(description="Fully update a book."),
    partial_update=extend_schema(description="Partially update a book."),
    destroy=extend_schema(description="Delete a book from the library."),
)
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        if self.action == "retrieve":
            return BookDetailSerializer
        return BookSerializer
