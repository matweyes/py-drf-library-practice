from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing

BORROWING_LIST_URL = reverse("borrowings:borrowing-list")


def detail_url(borrowing_id):
    return reverse("borrowings:borrowing-detail", args=[borrowing_id])


def return_url(borrowing_id):
    return reverse("borrowings:borrowing-return-borrowing", args=[borrowing_id])


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


def sample_borrowing(user, book=None, **params):
    if book is None:
        book = sample_book()
    defaults = {
        "expected_return_date": date.today() + timedelta(days=14),
        "book": book,
        "user": user,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


class AnonymousBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_borrowings_unauthorized(self):
        res = self.client.get(BORROWING_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_borrowing_unauthorized(self):
        user = get_user_model().objects.create_user("user@test.com", "testpass123")
        borrowing = sample_borrowing(user)

        res = self.client.get(detail_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_borrowing_unauthorized(self):
        book = sample_book()
        payload = {
            "book": book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }
        res = self.client.post(BORROWING_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com", "testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_list_borrowings(self):
        sample_borrowing(self.user)
        sample_borrowing(self.user)

        res = self.client.get(BORROWING_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_list_serializer_has_summary_fields(self):
        sample_borrowing(self.user)

        res = self.client.get(BORROWING_LIST_URL)

        data = res.data[0]
        self.assertIn("book_title", data)
        self.assertIn("book_author", data)
        self.assertIn("borrow_date", data)
        self.assertIn("expected_return_date", data)
        self.assertIn("actual_return_date", data)
        self.assertNotIn("book", data)

    def test_retrieve_borrowing(self):
        borrowing = sample_borrowing(self.user)

        res = self.client.get(detail_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], borrowing.id)

    def test_detail_serializer_has_nested_book(self):
        borrowing = sample_borrowing(self.user)

        res = self.client.get(detail_url(borrowing.id))

        self.assertIn("book", res.data)
        self.assertIn("title", res.data["book"])
        self.assertIn("author", res.data["book"])
        self.assertIn("daily_fee", res.data["book"])

    def test_borrowing_model_is_active_property(self):
        active = sample_borrowing(self.user)
        returned = sample_borrowing(
            self.user,
            actual_return_date=date.today(),
        )

        self.assertTrue(active.is_active)
        self.assertFalse(returned.is_active)

    def test_borrowing_model_constraint_expected_before_borrow(self):
        with self.assertRaises(Exception):
            Borrowing.objects.create(
                borrow_date=date.today(),
                expected_return_date=date.today() - timedelta(days=1),
                book=sample_book(),
                user=self.user,
            )

    def test_create_borrowing(self):
        book = sample_book(inventory=5)
        payload = {
            "book": book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }

        res = self.client.post(BORROWING_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        borrowing = Borrowing.objects.get(id=res.data["id"])
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, book)

    def test_create_borrowing_decrements_inventory(self):
        book = sample_book(inventory=5)
        payload = {
            "book": book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }

        self.client.post(BORROWING_LIST_URL, payload)

        book.refresh_from_db()
        self.assertEqual(book.inventory, 4)

    def test_create_borrowing_zero_inventory_rejected(self):
        book = sample_book(inventory=0)
        payload = {
            "book": book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }

        res = self.client.post(BORROWING_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_borrowing_denied_if_overdue(self):
        sample_borrowing(
            self.user,
            expected_return_date=date.today() - timedelta(days=1),
        )
        book = sample_book(inventory=5)
        payload = {
            "book": book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }

        res = self.client.post(BORROWING_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_borrowing_allowed_if_overdue_returned(self):
        sample_borrowing(
            self.user,
            expected_return_date=date.today() - timedelta(days=1),
            actual_return_date=date.today(),
        )
        book = sample_book(inventory=5)
        payload = {
            "book": book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }

        res = self.client.post(BORROWING_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_list_shows_only_own_borrowings(self):
        other_user = get_user_model().objects.create_user(
            "other@test.com", "testpass123"
        )
        sample_borrowing(self.user)
        sample_borrowing(other_user)

        res = self.client.get(BORROWING_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_filter_is_active_true(self):
        sample_borrowing(self.user)
        sample_borrowing(self.user, actual_return_date=date.today())

        res = self.client.get(BORROWING_LIST_URL, {"is_active": "true"})

        self.assertEqual(len(res.data), 1)
        self.assertIsNone(res.data[0]["actual_return_date"])

    def test_filter_is_active_false(self):
        sample_borrowing(self.user)
        sample_borrowing(self.user, actual_return_date=date.today())

        res = self.client.get(BORROWING_LIST_URL, {"is_active": "false"})

        self.assertEqual(len(res.data), 1)
        self.assertIsNotNone(res.data[0]["actual_return_date"])

    def test_user_id_filter_ignored_for_non_admin(self):
        other_user = get_user_model().objects.create_user(
            "other@test.com", "testpass123"
        )
        sample_borrowing(self.user)
        sample_borrowing(other_user)

        res = self.client.get(BORROWING_LIST_URL, {"user_id": other_user.id})

        self.assertEqual(len(res.data), 1)

    def test_is_overdue_filter_ignored_for_non_admin(self):
        sample_borrowing(
            self.user,
            expected_return_date=date.today() - timedelta(days=1),
        )
        sample_borrowing(
            self.user,
            expected_return_date=date.today() + timedelta(days=7),
        )

        res = self.client.get(BORROWING_LIST_URL, {"is_overdue": "true"})

        self.assertEqual(len(res.data), 2)

    def test_return_borrowing(self):
        book = sample_book(inventory=5)
        borrowing = sample_borrowing(self.user, book=book)

        res = self.client.post(return_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, date.today())

    def test_return_borrowing_increments_inventory(self):
        book = sample_book(inventory=5)
        borrowing = sample_borrowing(self.user, book=book)

        self.client.post(return_url(borrowing.id))

        book.refresh_from_db()
        self.assertEqual(book.inventory, 6)

    def test_return_borrowing_twice_rejected(self):
        borrowing = sample_borrowing(
            self.user, actual_return_date=date.today()
        )

        res = self.client.post(return_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_borrowing_model_str(self):
        book = sample_book(title="Django Basics")
        borrowing = sample_borrowing(self.user, book=book)

        self.assertIn("Django Basics", str(borrowing))
        self.assertIn(self.user.email, str(borrowing))


class AdminBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            "admin@test.com", "testpass123", is_staff=True
        )
        self.client.force_authenticate(self.admin)

    def test_admin_sees_all_borrowings(self):
        other_user = get_user_model().objects.create_user(
            "other@test.com", "testpass123"
        )
        sample_borrowing(self.admin)
        sample_borrowing(other_user)

        res = self.client.get(BORROWING_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_admin_filter_by_user_id(self):
        other_user = get_user_model().objects.create_user(
            "other@test.com", "testpass123"
        )
        sample_borrowing(self.admin)
        sample_borrowing(other_user)

        res = self.client.get(BORROWING_LIST_URL, {"user_id": other_user.id})

        self.assertEqual(len(res.data), 1)

    def test_admin_filter_is_overdue(self):
        sample_borrowing(
            self.admin,
            expected_return_date=date.today() - timedelta(days=1),
        )
        sample_borrowing(
            self.admin,
            expected_return_date=date.today() + timedelta(days=7),
        )

        res = self.client.get(BORROWING_LIST_URL, {"is_overdue": "true"})

        self.assertEqual(len(res.data), 1)

    def test_admin_is_overdue_excludes_returned(self):
        sample_borrowing(
            self.admin,
            expected_return_date=date.today() - timedelta(days=1),
            actual_return_date=date.today(),
        )

        res = self.client.get(BORROWING_LIST_URL, {"is_overdue": "true"})

        self.assertEqual(len(res.data), 0)
