from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.utils.timezone import now
from rest_framework.test import APITestCase
from rest_framework import status

from library.factory import TestFactory
from library.models import Member, Book


# Create your tests here.
class AuthorApiTest(APITestCase):
    fixtures = ['authors.json']

    base_url = reverse_lazy('api:author-list')

    def test_author_list(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json = response.json()
        self.assertEqual(len(json), 3)

    def test_author_create(self):
        response = self.client.post(self.base_url, data=TestFactory.author_factory())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        json = response.json()
        self.assertEqual(json['first_name'], 'John')

    def test_author_detail(self):
        response = self.client.get(reverse_lazy('api:author-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json = response.json()
        self.assertEqual(json['first_name'], 'Author 1')


# Create your tests here.
class BookApiTest(APITestCase):
    fixtures = ['books.json', 'authors.json']

    base_url = reverse_lazy('api:book-list')
    detail_url = 'api:book-detail'

    def test_book_list(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json = response.json()
        self.assertEqual(len(json), 3)

    def test_book_create(self):
        response = self.client.post(self.base_url, data=TestFactory.book_factory())
        json = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json['title'], 'Introduction to Django with Python')

    def test_book_detail(self):
        response = self.client.get(reverse_lazy(self.detail_url, kwargs={'pk': 1}))
        json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json['id'], 1)
        self.assertEqual(json['title'], 'Programing with Python')

    def _create_user(self):
        return User.objects.create_user(
            **TestFactory.user_factory()
        )

    def test_book_loan(self):

        user = self._create_user()
        member = Member.objects.create(user=user, membership_date=now())
        book_id = 1

        url = reverse_lazy(self.detail_url, kwargs={'pk': book_id})
        url += 'loan/'
        response = self.client.post(url, data={'member_id': member.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check available copies
        book = Book.objects.get(id=book_id)
        self.assertEqual(book.available_copies, 4)
        self.assertEqual(book.loans.count(), 1)

        # Check member
        member.refresh_from_db()
        self.assertEqual(member.loans.count(), 1)
