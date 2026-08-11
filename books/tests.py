from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookListSerializer, BookDetailSerializer

BOOK_LIST_URL = reverse("books:book-list")


def detail_url(book_id):
    return reverse("books:book-detail", args=[book_id])


def sample_book(**params):
    defaults = {
        "title": "Test Book",
        "author": "Test Author",
        "cover": Book.CoverType.HARD,
        "inventory": 10,
        "daily_fee": Decimal("1.50"),
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class BookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_books(self):
        sample_book(title="Book A")
        sample_book(title="Book B")

        res = self.client.get(BOOK_LIST_URL)

        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_book(self):
        book = sample_book()

        res = self.client.get(detail_url(book.id))

        serializer = BookDetailSerializer(book)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_serializer_excludes_daily_fee(self):
        sample_book()

        res = self.client.get(BOOK_LIST_URL)

        self.assertNotIn("daily_fee", res.data[0])

    def test_detail_serializer_includes_daily_fee(self):
        book = sample_book()

        res = self.client.get(detail_url(book.id))

        self.assertIn("daily_fee", res.data)

    def test_create_book(self):
        payload = {
            "title": "New Book",
            "author": "Author",
            "cover": "HARD",
            "inventory": 5,
            "daily_fee": "2.00",
        }
        res = self.client.post(BOOK_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(id=res.data["id"])
        self.assertEqual(book.title, "New Book")
        self.assertEqual(book.daily_fee, Decimal("2.00"))

    def test_create_book_invalid_cover(self):
        payload = {
            "title": "Bad Cover",
            "author": "Author",
            "cover": "LEATHER",
            "inventory": 5,
            "daily_fee": "2.00",
        }
        res = self.client.post(BOOK_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_book(self):
        book = sample_book()

        res = self.client.put(detail_url(book.id), {
            "title": "Updated Title",
            "author": "Updated Author",
            "cover": "SOFT",
            "inventory": 20,
            "daily_fee": "3.50",
        })

        book.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(book.title, "Updated Title")
        self.assertEqual(book.cover, Book.CoverType.SOFT)
        self.assertEqual(book.inventory, 20)

    def test_partial_update_book(self):
        book = sample_book()

        res = self.client.patch(detail_url(book.id), {"inventory": 0})

        book.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(book.inventory, 0)

    def test_delete_book(self):
        book = sample_book()

        res = self.client.delete(detail_url(book.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())
