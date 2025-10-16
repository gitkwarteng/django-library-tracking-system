import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils.timezone import now
from rest_framework.test import APITestCase
from rest_framework import status

from library.factory import TestFactory
from library.models import Member, Book, Loan
from library.operations import get_loan_overdue_members, get_member_overdue_book_title_values
from library.tasks import check_overdue_loans


def create_test_member(**kwargs):
    user = User.objects.create_user(
        **TestFactory.user_factory(**kwargs)
    )

    return Member.objects.create(user=user, membership_date=now())

# Create your tests here.
class AuthorApiTest(APITestCase):
    fixtures = ['authors.json']

    base_url = reverse_lazy('api:author-list')

    def test_author_list(self):
        response = self.client.get(self.base_url)
        json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json['count'], 3)
        self.assertEqual(len(json['results']), 3)

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


class BookApiTest(APITestCase):
    fixtures = ['books.json', 'authors.json']

    base_url = reverse_lazy('api:book-list')
    detail_url = 'api:book-detail'

    def test_book_list(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json = response.json()
        self.assertEqual(json['count'], 3)
        self.assertEqual(len(json['results']), 3)

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

    def test_book_loan(self):

        member = create_test_member()
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


class OperationsTest(TestCase):
    fixtures = ['books.json', 'authors.json']

    def test_get_overdue_loan_members(self):
        today = now()
        member = create_test_member()
        # Create overdue loan
        Loan.objects.create(
            member=member,
            book_id=1,
            loan_date=today - timedelta(days=15),
            is_returned=False
        )

        overdue = get_loan_overdue_members()

        self.assertEqual(len(overdue), 1)

    def test_get_member_overdue_book_title_values(self):
        today = now()
        member = create_test_member()
        # Create overdue loan
        Loan.objects.create(
            member=member,
            book_id=1,
            loan_date=today - timedelta(days=15),
            is_returned=False
        )

        title_values = get_member_overdue_book_title_values(member_id=member.id)
        self.assertEqual(len(title_values), 1)


class OverdueTaskTest(TestCase):
    fixtures = ['books.json', 'authors.json']

    def test_check_overdue_loans_task(self):
        today = now()
        member = create_test_member()
        # Create overdue loan
        Loan.objects.create(
            member=member,
            book_id=1,
            loan_date=today - timedelta(days=15),
            is_returned=False
        )

        check_overdue_loans()

        # Verify task was queued or executed
        self.assertEqual(len(mail.outbox), 1)


class LoanApiTest(APITestCase):
    fixtures = ['books.json', 'authors.json']

    base_url = reverse_lazy('api:loan-list')
    detail_url = 'api:loan-detail'


    def test_loan_create(self):
        member = create_test_member()
        loan_data = {'member_id': member.id, 'book_id': 1}
        response = self.client.post(self.base_url, data=loan_data)
        json = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json['member']['id'], 1)
        self.assertEqual(json['book']['id'], 1)

    def test_loan_extend(self):

        member = create_test_member()
        extend_data = {'additional_days': 5}

        today = now()
        loan = Loan.objects.create(
            member=member,
            book_id=1,
            loan_date=today
        )

        url = reverse_lazy(self.detail_url, kwargs={'pk': loan.id})
        url += 'extend_due_date/'
        response = self.client.post(url, data=extend_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        loan.refresh_from_db()
        self.assertEqual(loan.due_date, (today + timedelta(days=19)).date())

    def test_loan_extend_zero_days(self):

        member = create_test_member()
        extend_data = {'additional_days': 0}

        today = now()
        loan = Loan.objects.create(
            member=member,
            book_id=1,
            loan_date=today
        )

        url = reverse_lazy(self.detail_url, kwargs={'pk': loan.id})
        url += 'extend_due_date/'
        response = self.client.post(url, data=extend_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_loan_extend_negative_days(self):

        member = create_test_member()
        extend_data = {'additional_days': -5}

        today = now()
        loan = Loan.objects.create(
            member=member,
            book_id=1,
            loan_date=today
        )

        url = reverse_lazy(self.detail_url, kwargs={'pk': loan.id})
        url += 'extend_due_date/'
        response = self.client.post(url, data=extend_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MemberAPITest(APITestCase):
    fixtures = ['books.json', 'authors.json']

    base_url = reverse_lazy('api:member-list')

    def test_top_active_members(self):

        member1 = create_test_member()
        member2 = create_test_member(first_name='John', last_name='Doe', username='johndoe')

        today = now()
        # Create 5 loans
        member2_loans = [
            Loan(
                member=member2,
                book_id=random.randint(1, 3),
                loan_date=today
            )
            for _ in range(5)
        ]

        # Create 3 loans
        member1_loans = [
            Loan(
                member=member1,
                book_id=random.randint(1, 3),
                loan_date=today
            )
            for _ in range(3)
        ]

        Loan.objects.bulk_create(member1_loans + member2_loans)

        url = self.base_url + 'top-active/'
        response = self.client.get(url)
        json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check 2 results returned
        self.assertEqual(len(json), 2)
        # Check first result is member 2
        self.assertEqual(json[0]['id'], member2.id)
