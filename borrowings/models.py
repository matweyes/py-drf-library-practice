from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="borrowings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )

    class Meta:
        ordering = ["-borrow_date"]

    def clean(self):
        if (
            self.borrow_date
            and self.expected_return_date
            and self.expected_return_date < self.borrow_date
        ):
            raise ValidationError(
                {"expected_return_date": "Expected return date must be after borrow date."}
            )
        if (
            self.actual_return_date
            and self.borrow_date
            and self.actual_return_date < self.borrow_date
        ):
            raise ValidationError(
                {"actual_return_date": "Actual return date must be after borrow date."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.actual_return_date is None

    def __str__(self):
        return f"{self.book.title} — {self.user.email} ({self.borrow_date})"
