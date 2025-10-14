from typing import List
from itertools import islice

from celery import shared_task
from django.core.cache import cache
from django.db.models import Exists, OuterRef
from django.utils.timezone import now

from .models import Loan, Member
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass


@shared_task(queue='schedule')
def send_batch_overdue_notification(members: List[Member]):
    """
    Send email reminder to members with over due loans in batch

    Args:
        members: list of members
    """
    email_subject = 'Loan Overdue Reminder'

    for member in members:
        # Get member loans
        loans = Loan.objects.filter(
            member_id=member.id,
            is_returned=False,
            due_date__date__lt=now().date(),
        ).select_related(
             'book'
        ).values(
            'book__title'
        )

        overdue_books = "\n".join([loan['book__title'] for loan in loans])

        username = member.user.first_name
        email = member.user.email
        message = f'Hello {username},\n\nThese books are overdue \n "{overdue_books}".\n Please return them.'
        send_mail(
            subject=email_subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )



@shared_task
def check_overdue_loans():
    """
    Check overdue loans.
    """

    # Implement lock to prevent task overlap
    overdue_task_key = 'overdue_loans_task'

    # Check if cache exists
    if cache.get(overdue_task_key):
        return "Task is running."

    cache.set(overdue_task_key, True, timeout=300)

    over_due_subquery = Loan.objects.filter(
        memer_id=OuterRef('id'),
        due_date__lte=now(),
        is_returned=False
    )

    overdue_members = Member.objects.annotate(
        has_overdure=Exists(over_due_subquery)
    ).select_related(
        'user'
    ).filter(
        has_overdure=True,
    ).only('id', 'user').iterator(chunk_size=500)

    batch_size = 50

    while True:
        chunk = list(islice(overdue_members, batch_size))
        if not chunk:
            break

        send_batch_overdue_notification.delay(chunk)
