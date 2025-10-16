from typing import List, Dict
from itertools import islice

from celery import shared_task
from django.core.cache import cache

from .models import Loan
from django.core.mail import send_mail
from django.conf import settings

from .operations import get_loan_overdue_members, get_member_overdue_book_title_values


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
def send_batch_overdue_notification(members: List[Dict[str, str]]):
    """
    Send email reminder to members with overdue loans in batch

    Args:
        members: list of member dictionary with id, name, and email.
    """
    email_subject = 'Book Loan Overdue Reminder'

    for member in members:
        # Get member loans
        member_id:int = int(member['id'])
        email:str = member['email']

        if not member_id or email:
            continue

        # Get books
        books = get_member_overdue_book_title_values(member_id)

        overdue_books = "\n".join([book['book__title'] for book in books])

        message = f'Hello {member["name"]},\n\nThese books are overdue \n "{overdue_books}".\n Please return them.'
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

    try:
        overdue_members = get_loan_overdue_members().iterator(chunk_size=500)

        batch_size = 50

        while True:
            chunk = list(islice(overdue_members, batch_size))
            if not chunk:
                break

            # Get member data list
            members_data = [{'id':m.id, 'name':m.user.first_name, 'email':m.user.email} for m in chunk]
            send_batch_overdue_notification.delay(members_data)
    finally:
        cache.delete(overdue_task_key)
