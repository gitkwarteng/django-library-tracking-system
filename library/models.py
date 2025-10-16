from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

from library.choices import BookGenreChoices


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    biography = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ['first_name']

class Book(models.Model):

    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, related_name='books', on_delete=models.CASCADE)
    isbn = models.CharField(max_length=13, unique=True)
    genre = models.CharField(
        max_length=50, choices=BookGenreChoices.choices, default=BookGenreChoices.OTHER)
    available_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ['title']

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    membership_date = models.DateField(auto_now_add=True)
    # Add more fields if necessary

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"
        ordering = ['-membership_date']

class Loan(models.Model):
    book = models.ForeignKey(Book, related_name='loans', on_delete=models.CASCADE)
    member = models.ForeignKey(Member, related_name='loans', on_delete=models.CASCADE)
    loan_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.book.title} loaned to {self.member.user.username}"

    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
        ordering = ['-loan_date']

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = (self.loan_date or now()) + timedelta(days=14)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return self.due_date < now().date() if self.due_date else self.loan_date + timedelta(days=14) < now()
