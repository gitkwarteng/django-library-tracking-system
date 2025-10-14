from django.db import models


class BookGenreChoices(models.TextChoices):
    FICTION = 'fiction', 'Fiction'
    SCIENCE = 'science', 'Science'
    NON_FICTION = 'nonfiction', 'Non-Fiction'
    SCIENCE_FICTION = 'sci-fi', 'Sci-Fi'
    PROGRAMMING = 'dev', 'Software Development'
    BIOGRAPHY = 'Biography'
    OTHER = 'Other'